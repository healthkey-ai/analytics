from django.db import models


class PatientInfo(models.Model):
    """Read-only mirror of ctomop.patient_info. managed=False — no migrations."""

    # demographics
    patient_age = models.IntegerField(null=True)
    gender = models.CharField(max_length=2, null=True)
    race = models.TextField(null=True)
    ethnicity = models.TextField(null=True)
    country = models.CharField(max_length=255, null=True)
    region = models.CharField(max_length=255, null=True)
    postal_code = models.CharField(max_length=20, null=True)
    date_of_birth = models.DateField(null=True)
    smoking_status = models.CharField(max_length=50, null=True)

    # disease
    disease = models.TextField(null=True)
    disease_slug = models.CharField(max_length=100, null=True)
    stage = models.TextField(null=True)
    diagnosis_date = models.DateField(null=True)
    condition_clinical_status = models.CharField(max_length=50, null=True)

    # performance
    karnofsky_performance_score = models.IntegerField(null=True)
    ecog_performance_status = models.IntegerField(null=True)

    # comorbidities / eligibility
    no_other_active_malignancies = models.BooleanField(default=True)
    no_pre_existing_conditions = models.BooleanField(null=True)
    preexisting_conditions = models.JSONField(null=True)
    peripheral_neuropathy_grade = models.IntegerField(null=True)

    # cytogenetics / molecular
    cytogenic_markers = models.TextField(null=True)
    genetic_mutations = models.JSONField(default=list)
    tp53_disruption = models.BooleanField(null=True)
    stem_cell_transplant_history = models.JSONField(null=True)
    plasma_cell_leukemia = models.BooleanField(null=True)

    # MM-specific disease characteristics
    clonal_plasma_cells = models.IntegerField(null=True)
    measurable_disease_imwg = models.BooleanField(null=True)
    meets_crab = models.BooleanField(null=True)
    bone_lesions = models.TextField(null=True)
    bone_imaging_result = models.BooleanField(default=False)
    kappa_flc = models.IntegerField(null=True)
    lambda_flc = models.IntegerField(null=True)
    monoclonal_protein_serum = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    monoclonal_protein_urine = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # labs — CBC
    hemoglobin_g_dl = models.DecimalField(max_digits=5, decimal_places=1, null=True)
    platelet_count = models.IntegerField(null=True)
    wbc_count_thousand_per_ul = models.DecimalField(max_digits=6, decimal_places=1, null=True)
    anc_thousand_per_ul = models.DecimalField(max_digits=6, decimal_places=1, null=True)

    # labs — renal / electrolytes
    serum_creatinine_mg_dl = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    egfr_ml_min_173m2 = models.DecimalField(max_digits=6, decimal_places=1, null=True)
    serum_calcium_mg_dl = models.DecimalField(max_digits=5, decimal_places=1, null=True)

    # labs — liver / protein
    albumin_g_dl = models.DecimalField(max_digits=5, decimal_places=1, null=True)
    ast_u_l = models.IntegerField(null=True)
    alt_u_l = models.IntegerField(null=True)
    alkaline_phosphatase_u_l = models.IntegerField(null=True)
    bilirubin_total_mg_dl = models.DecimalField(max_digits=5, decimal_places=1, null=True)

    # labs — myeloma-specific
    beta2_microglobulin = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    ldh_u_l = models.IntegerField(null=True)

    # breast cancer specific
    estrogen_receptor_status = models.TextField(null=True)
    progesterone_receptor_status = models.TextField(null=True)
    her2_status = models.TextField(null=True)
    tnbc_status = models.BooleanField(null=True)
    tumor_stage = models.TextField(null=True)
    nodes_stage = models.TextField(null=True)
    distant_metastasis_stage = models.TextField(null=True)

    # outcomes / follow-up
    death_date = models.DateField(null=True)

    # treatment
    prior_therapy = models.TextField(null=True)
    therapy_lines_count = models.IntegerField(null=True)
    relapse_count = models.IntegerField(null=True)
    treatment_refractory_status = models.CharField(max_length=255, null=True)
    last_treatment = models.DateField(null=True)

    first_line_therapy = models.TextField(null=True)
    first_line_start_date = models.DateField(null=True)
    first_line_end_date = models.DateField(null=True)
    first_line_date = models.DateField(null=True)
    first_line_outcome = models.TextField(null=True)
    first_line_intent = models.CharField(max_length=50, null=True)
    first_line_discontinuation_reason = models.CharField(max_length=50, null=True)

    second_line_therapy = models.TextField(null=True)
    second_line_start_date = models.DateField(null=True)
    second_line_end_date = models.DateField(null=True)
    second_line_date = models.DateField(null=True)
    second_line_outcome = models.TextField(null=True)
    second_line_intent = models.CharField(max_length=50, null=True)

    later_therapy = models.TextField(null=True)
    later_start_date = models.DateField(null=True)
    later_end_date = models.DateField(null=True)
    later_date = models.DateField(null=True)
    later_outcome = models.TextField(null=True)
    later_intent = models.CharField(max_length=50, null=True)
    later_therapies = models.JSONField(default=list)

    supportive_therapies = models.TextField(null=True)
    supportive_therapy_start_date = models.DateField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "patient_info"

    def __str__(self):
        return f"PatientInfo {self.pk} – {self.disease}"
