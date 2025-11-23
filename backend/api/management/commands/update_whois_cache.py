import time

from django.core.management.base import BaseCommand

from api.endpoints.ip_info.services import get_whois_info
from api.models import IPGeolocation


class Command(BaseCommand):
    help = "Update existing IP geolocation cache with WHOIS information"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of IPs to process in each batch (default: 10)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.0,
            help="Delay in seconds between each WHOIS lookup (default: 1.0)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of IPs to process (default: all)",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip IPs that already have WHOIS information",
        )
        parser.add_argument(
            "--order-by-hits",
            action="store_true",
            help="Process IPs in order of hit count (most accessed first)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        delay = options["delay"]
        limit = options["limit"]
        skip_existing = options["skip_existing"]
        order_by_hits = options["order_by_hits"]

        # Get IPs that need WHOIS information
        if skip_existing:
            qs = IPGeolocation.objects.filter(whois_raw__isnull=True)
        else:
            qs = IPGeolocation.objects.all()

        # Order by hit count if requested
        if order_by_hits:
            qs = qs.order_by("-hit_count")

        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(
            self.style.SUCCESS(f"Found {total} IPs to process")
        )

        processed = 0
        updated = 0
        failed = 0

        for geo in qs:
            processed += 1

            self.stdout.write(
                f"[{processed}/{total}] Processing {geo.ip_address}...",
                ending="",
            )

            # Get WHOIS information
            whois_info = get_whois_info(geo.ip_address)

            if whois_info:
                # Update the record
                geo.whois_raw = whois_info.get("raw")
                geo.whois_netname = whois_info.get("netname")
                geo.whois_org_name = whois_info.get("org_name")
                geo.whois_country = whois_info.get("country")
                geo.whois_net_range = whois_info.get("net_range")
                geo.save(
                    update_fields=[
                        "whois_raw",
                        "whois_netname",
                        "whois_org_name",
                        "whois_country",
                        "whois_net_range",
                    ]
                )
                updated += 1
                self.stdout.write(self.style.SUCCESS(" ✓"))
            else:
                failed += 1
                self.stdout.write(self.style.WARNING(" ✗ (failed)"))

            # Delay between requests to avoid rate limiting
            if processed % batch_size == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Batch completed. Sleeping {delay}s..."
                    )
                )
                time.sleep(delay)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"Processing complete!\n"
                f"  Total processed: {processed}\n"
                f"  Successfully updated: {updated}\n"
                f"  Failed: {failed}"
            )
        )
