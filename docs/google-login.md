# Plan: Google OAuth Signup/Login

## Context
PRism currently supports email+password auth only. Adding Google OAuth lets users sign in with their Google account — lower friction and no password to manage. The `Identity` model already has `issuer`/`sub`/`uid` fields designed for multi-provider auth, and `IdentityManager.get_or_create_from_claims()` already handles federated identity creation. Auth is session-based (no JWT).

## Branch
Create `feature/google-oauth` from `dev`.

---

## Backend Changes

### 1. `backend/requirements.txt`
Add:
```
google-auth>=2.29
```
(`google-auth` validates Google ID tokens server-side without needing `requests-oauthlib`.)

### 2. `backend/accounts/views.py`
Add `google_login_view`:
```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def google_login_view(request):
    credential = request.data.get("credential", "")
    if not credential:
        return Response({"detail": "Missing credential."}, status=400)

    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    try:
        claims = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except ValueError as exc:
        return Response({"detail": f"Invalid token: {exc}"}, status=400)

    email = claims.get("email", "")
    name  = claims.get("name", "")
    sub   = claims["sub"]

    user = Identity.objects.get_or_create_from_claims(
        issuer="accounts.google.com",
        sub=sub,
        email=email,
        name=name,
    )

    # Ensure UserProfile exists
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"organization": "", "role": UserProfile.ROLE_USER},
    )

    request.session.cycle_key()
    login(request, user, backend="accounts.backends.EmailBackend")
    get_token(request)
    return Response(_user_data(user))
```

### 3. `backend/accounts/urls.py`
Add:
```python
path("google-login/", views.google_login_view),
```

### 4. `backend/analytics_project/settings.py`
Add near other env-var reads:
```python
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
```

### 5. `.env` (local) and Render env vars
Add: `GOOGLE_OAUTH_CLIENT_ID=<your_client_id>.apps.googleusercontent.com`

### 6. Backend Tests — `backend/accounts/tests/test_google_login.py` (new)
```python
from unittest.mock import patch
from django.test import TestCase

class GoogleLoginTests(TestCase):
    VALID_CLAIMS = {
        "sub": "12345", "email": "test@gmail.com",
        "name": "Test User", "aud": "client-id",
    }

    @patch("accounts.views.id_token.verify_oauth2_token")
    def test_valid_token_creates_user_and_logs_in(self, mock_verify):
        mock_verify.return_value = self.VALID_CLAIMS
        r = self.client.post("/api/auth/google-login/", {"credential": "tok"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["email"], "test@gmail.com")

    @patch("accounts.views.id_token.verify_oauth2_token", side_effect=ValueError("bad"))
    def test_invalid_token_returns_400(self, mock_verify):
        r = self.client.post("/api/auth/google-login/", {"credential": "bad"}, content_type="application/json")
        self.assertEqual(r.status_code, 400)

    @patch("accounts.views.id_token.verify_oauth2_token")
    def test_existing_google_user_logs_in(self, mock_verify):
        mock_verify.return_value = self.VALID_CLAIMS
        # First call creates user
        self.client.post("/api/auth/google-login/", {"credential": "tok"}, content_type="application/json")
        self.client.logout()
        # Second call reuses existing Identity
        r = self.client.post("/api/auth/google-login/", {"credential": "tok"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
```

---

## Frontend Changes

### 7. Install `@react-oauth/google`
```bash
cd frontend && npm install @react-oauth/google
```

### 8. `frontend/src/api/client.ts`
Add:
```typescript
export async function googleLogin(credential: string) {
  const { data } = await api.post('/auth/google-login/', { credential })
  return data
}
```

### 9. `frontend/src/hooks/useAuth.ts`
Add to `AuthState` interface:
```typescript
googleLogin: (credential: string) => Promise<void>
```
Add implementation:
```typescript
const googleLogin = useCallback(async (credential: string) => {
  const data = await api.googleLogin(credential)
  setUser(data)
}, [])
```
Return it in the object.

### 10. `frontend/src/main.tsx` (app root)
Wrap with `GoogleOAuthProvider`:
```tsx
import { GoogleOAuthProvider } from '@react-oauth/google'

<GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
  <App />
</GoogleOAuthProvider>
```

### 11. `frontend/src/components/Auth/LoginPage.tsx`
Add Google button with "or" divider, below existing form fields and above the error display:
```tsx
import { GoogleLogin } from '@react-oauth/google'

<div className="flex items-center gap-2">
  <div className="flex-1 h-px bg-slate-700" />
  <span className="text-xs text-slate-500">or</span>
  <div className="flex-1 h-px bg-slate-700" />
</div>
<div className="flex justify-center">
  <GoogleLogin
    onSuccess={async (resp) => {
      if (!resp.credential) return
      setSubmitting(true)
      try { await auth.googleLogin(resp.credential) }
      catch { setError('Google sign-in failed. Please try again.') }
      finally { setSubmitting(false) }
    }}
    onError={() => setError('Google sign-in failed. Please try again.')}
    useOneTap
    theme="filled_black"
    shape="pill"
    text={mode === 'login' ? 'signin_with' : 'signup_with'}
  />
</div>
```

### 12. `frontend/.env` (local dev)
```
VITE_GOOGLE_CLIENT_ID=<your_client_id>.apps.googleusercontent.com
```

---

## Critical Files
| File | Change |
|---|---|
| `backend/requirements.txt` | Add `google-auth` |
| `backend/accounts/views.py` | Add `google_login_view` |
| `backend/accounts/urls.py` | Wire `google-login/` route |
| `backend/analytics_project/settings.py` | Add `GOOGLE_OAUTH_CLIENT_ID` setting |
| `backend/accounts/tests/test_google_login.py` | New test file |
| `frontend/src/api/client.ts` | Add `googleLogin()` |
| `frontend/src/hooks/useAuth.ts` | Add `googleLogin` to state |
| `frontend/src/main.tsx` | Wrap with `GoogleOAuthProvider` |
| `frontend/src/components/Auth/LoginPage.tsx` | Add Google button + divider |
| `frontend/.env` | Add `VITE_GOOGLE_CLIENT_ID` |

---

## Prerequisites (user must do before testing)
1. Create a Google OAuth 2.0 Client ID at Google Cloud Console → APIs & Services → Credentials → Web application
2. Add authorized JS origins: `http://localhost:5173`, `https://prism-dev.onrender.com`, `https://prism.onrender.com`
3. Add the Client ID to local `.env` and Render environment variables

---

## Verification
1. `cd backend && pytest accounts/tests/test_google_login.py --ds=analytics_project.test_settings -q` → all 3 tests pass
2. Open app → see "or" divider + Google button on both Sign In and Sign Up tabs
3. Click Google button → popup → sign in → dashboard loads
4. Revisit page → still logged in (session persists)
5. Sign in again with same Google account → logs in without creating duplicate Identity row
