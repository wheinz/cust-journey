from django.db import models
from django.urls import reverse


class Phase(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('journey:phase_detail', kwargs={'pk': self.pk})


class JourneyPhase(models.Model):
    phase = models.ForeignKey(
        Phase, on_delete=models.CASCADE, related_name='journey_phases'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['phase', 'slug']

    def __str__(self):
        return f'{self.phase.name} → {self.name}'

    def get_absolute_url(self):
        return reverse('journey:journey_phase_detail', kwargs={'pk': self.pk})


class Step(models.Model):
    journey_phase = models.ForeignKey(
        JourneyPhase, on_delete=models.CASCADE, related_name='steps'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['journey_phase', 'slug']

    def __str__(self):
        return f'{self.journey_phase.phase.name} → {self.journey_phase.name} → {self.name}'

    def get_absolute_url(self):
        return reverse('journey:step_detail', kwargs={'pk': self.pk})


class Action(models.Model):
    step = models.ForeignKey(
        Step, on_delete=models.CASCADE, related_name='actions'
    )
    name = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500)
    order = models.PositiveIntegerField(default=0)
    is_drop_off = models.BooleanField(default=False)

    class Meta:
        ordering = ['step', 'order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('journey:action_detail', kwargs={'pk': self.pk})


class Touchpoint(models.Model):
    step = models.ForeignKey(
        Step, on_delete=models.CASCADE, related_name='touchpoints'
    )
    name = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['step', 'order', 'name']

    def __str__(self):
        return self.name
