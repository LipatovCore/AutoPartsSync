from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="\u0418\u043c\u044f")
    phone = models.CharField(max_length=32, blank=True, verbose_name="\u0422\u0435\u043b\u0435\u0444\u043e\u043d")
    note = models.TextField(blank=True, verbose_name="\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="\u0421\u043e\u0437\u0434\u0430\u043d")

    class Meta:
        verbose_name = "\u041a\u043b\u0438\u0435\u043d\u0442"
        verbose_name_plural = "\u041a\u043b\u0438\u0435\u043d\u0442\u044b"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Car(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="cars",
        verbose_name="\u041a\u043b\u0438\u0435\u043d\u0442",
    )
    brand = models.CharField(max_length=100, verbose_name="\u041c\u0430\u0440\u043a\u0430")
    model = models.CharField(max_length=100, verbose_name="\u041c\u043e\u0434\u0435\u043b\u044c")
    license_plate = models.CharField(max_length=20, blank=True, verbose_name="\u0413\u043e\u0441\u043d\u043e\u043c\u0435\u0440")
    vin = models.CharField(max_length=17, blank=True, verbose_name="VIN")
    note = models.TextField(blank=True, verbose_name="\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="\u0421\u043e\u0437\u0434\u0430\u043d")

    class Meta:
        verbose_name = "\u0410\u0432\u0442\u043e"
        verbose_name_plural = "\u0410\u0432\u0442\u043e"
        ordering = ["brand", "model"]

    def __str__(self):
        car_name = f"{self.brand} {self.model}"
        if self.license_plate:
            return f"{car_name} ({self.license_plate})"
        return car_name