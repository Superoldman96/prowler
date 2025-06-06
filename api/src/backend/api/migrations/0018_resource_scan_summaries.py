# Generated by Django 5.1.7 on 2025-05-05 10:01

import uuid

import django.db.models.deletion
import uuid6
from django.db import migrations, models

import api.rls


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0017_m365_provider"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResourceScanSummary",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("scan_id", models.UUIDField(db_index=True, default=uuid6.uuid7)),
                ("resource_id", models.UUIDField(db_index=True, default=uuid.uuid4)),
                ("service", models.CharField(max_length=100)),
                ("region", models.CharField(max_length=100)),
                ("resource_type", models.CharField(max_length=100)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.tenant"
                    ),
                ),
            ],
            options={
                "db_table": "resource_scan_summaries",
                "indexes": [
                    models.Index(
                        fields=["tenant_id", "scan_id", "service"],
                        name="rss_tenant_scan_svc_idx",
                    ),
                    models.Index(
                        fields=["tenant_id", "scan_id", "region"],
                        name="rss_tenant_scan_reg_idx",
                    ),
                    models.Index(
                        fields=["tenant_id", "scan_id", "resource_type"],
                        name="rss_tenant_scan_type_idx",
                    ),
                    models.Index(
                        fields=["tenant_id", "scan_id", "region", "service"],
                        name="rss_tenant_scan_reg_svc_idx",
                    ),
                    models.Index(
                        fields=["tenant_id", "scan_id", "service", "resource_type"],
                        name="rss_tenant_scan_svc_type_idx",
                    ),
                    models.Index(
                        fields=["tenant_id", "scan_id", "region", "resource_type"],
                        name="rss_tenant_scan_reg_type_idx",
                    ),
                ],
                "unique_together": {("tenant_id", "scan_id", "resource_id")},
            },
        ),
        migrations.AddConstraint(
            model_name="resourcescansummary",
            constraint=api.rls.RowLevelSecurityConstraint(
                "tenant_id",
                name="rls_on_resourcescansummary",
                statements=["SELECT", "INSERT", "UPDATE", "DELETE"],
            ),
        ),
    ]
