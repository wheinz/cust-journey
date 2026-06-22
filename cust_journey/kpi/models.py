from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class KPI(models.Model):
    class Level(models.TextChoices):
        BUSINESS_KPI = 'business_kpi', 'Business KPI'
        KPI = 'kpi', 'KPI'
        METRIC = 'metric', 'Metric'

    LEVEL_RANK = {
        'business_kpi': 2,
        'kpi': 1,
        'metric': 0,
    }

    class KPIType(models.TextChoices):
        BEHAVIORAL = 'behavioral', 'Behavioral'
        EXPERIENCE = 'experience', 'Experience'
        OPERATIONAL = 'operational', 'Operational'
        NA = 'n_a', 'n.a.'

    class MeasureStatus(models.TextChoices):
        YES = 'yes', 'Yes'
        NO = 'no', 'No'
        PARTIALLY = 'partially', 'Partially'

    class ReviewCadence(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        ANNUALLY = 'annually', 'Annually'

    class ImplementationPhase(models.TextChoices):
        DEFINED = 'defined', '1. Defined'
        DATA_SOURCED = 'data_sourced', '2. Data sourced'
        INSTRUMENTED = 'instrumented', '3. Instrumented'
        ACTIVELY_REVIEWED = 'actively_reviewed', '4. Actively reviewed'

    name = models.CharField(max_length=300)
    level = models.CharField(max_length=50, choices=Level.choices)
    kpi_type = models.CharField(max_length=50, choices=KPIType.choices, blank=True, default='')
    description = models.TextField(blank=True)
    owner = models.CharField(max_length=200, blank=True)
    why_important = models.TextField(blank=True)
    do_we_measure_it = models.CharField(
        max_length=20, choices=MeasureStatus.choices, default='no'
    )
    how_measure_it = models.TextField(blank=True)
    where_store = models.CharField(max_length=300, blank=True)
    review_cadence = models.CharField(
        max_length=20, choices=ReviewCadence.choices, blank=True, default=''
    )
    influences = models.TextField(blank=True)
    initiatives = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    impact = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        blank=True, null=True,
        help_text='1 = lowest, 5 = highest',
    )
    effort = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        blank=True, null=True,
        help_text='1 = least effort, 5 = most effort',
    )
    implementation_phase = models.CharField(
        max_length=30, choices=ImplementationPhase.choices,
        default='defined',
    )
    target_quarter = models.CharField(max_length=10, blank=True, default='')

    lifecycle_phase = models.ForeignKey(
        'journey.Phase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpis',
    )
    journey_phase = models.ForeignKey(
        'journey.JourneyPhase',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpis',
    )
    step = models.ForeignKey(
        'journey.Step',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpis',
    )

    contributes_to = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='supported_by',
        help_text='Higher-level KPIs this KPI contributes to',
    )

    class Meta:
        ordering = ['level', 'lifecycle_phase__order', 'kpi_type', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('kpi:kpi_detail', kwargs={'pk': self.pk})

    def get_ancestor_ids(self):
        ids = set()
        frontier = set(self.contributes_to.values_list('pk', flat=True))
        while frontier:
            ids.update(frontier)
            frontier = set(
                KPI.objects.filter(supported_by__pk__in=frontier)
                .values_list('pk', flat=True)
            ) - ids
        return ids

    def clean(self):
        super().clean()
        if self.pk:
            ancestors = self.get_ancestor_ids()
            if self.pk in ancestors:
                raise ValidationError(
                    'This KPI cannot contribute to itself (circular chain detected).'
                )
        for target in self.contributes_to.all():
            if self.LEVEL_RANK.get(self.level, 0) > self.LEVEL_RANK.get(target.level, 0):
                raise ValidationError(
                    f'"{self.name}" ({self.get_level_display()}) cannot contribute to '
                    f'"{target.name}" ({target.get_level_display()}). '
                    'Lower-level metrics can only contribute to higher or equal-level KPIs.'
                )
