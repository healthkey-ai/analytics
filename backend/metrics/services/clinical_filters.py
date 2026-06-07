from django.db.models import Q

# High-risk cytogenetic abnormalities per IMWG definition
HIGH_RISK_CYTO = (
    Q(cytogenic_markers__icontains='del(17p)') |
    Q(cytogenic_markers__icontains='t(4;14)') |
    Q(cytogenic_markers__icontains='t(14;16)')
)

HAS_SCT = (
    ~Q(stem_cell_transplant_history__isnull=True) &
    ~Q(stem_cell_transplant_history=[])
)

NO_SCT = (
    Q(stem_cell_transplant_history__isnull=True) |
    Q(stem_cell_transplant_history=[])
)
