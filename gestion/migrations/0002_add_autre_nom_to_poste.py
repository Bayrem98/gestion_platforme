from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0001_initial'),  # Vérifiez que ce numéro correspond à votre dernière migration
    ]

    operations = [
        migrations.AddField(
            model_name='poste',
            name='autre_nom',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Si autre, précisez'),
        ),
        migrations.AlterField(
            model_name='poste',
            name='nom',
            field=models.CharField(choices=[('COMPTABLE', 'Comptable'), ('RH', 'Ressources Humaines'), ('TECHNICIEN', 'Technicien'), ('DIRECTEUR', 'Directeur'), ('OUVRIER', 'Ouvrier'), ('AUTRE', 'Autre')], default='AUTRE', max_length=100),
        ),
    ]