import argparse
from typing import Any, Tuple, Dict, cast
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from campaigns.services import log_spend

class Command(BaseCommand):
    help = 'Log spend for a campaign. Usage: python manage.py log_spend <campaign_id> <amount>'

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('campaign_id', type=int, help='ID of the campaign')
        parser.add_argument('amount', type=str, help='Spend amount (decimal)')

    def handle(self, *args: Tuple[Any, ...], **options: Dict[str, Any]) -> None:
        campaign_id = cast(int, options['campaign_id'])
        amount_str = cast(str, options['amount'])

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise CommandError("Amount must be positive.")
        except InvalidOperation:
            raise CommandError(f"Invalid decimal amount: {amount_str}")

        try:
            log_spend(campaign_id, amount)
        except Exception as e:
            raise CommandError(f"Error logging spend: {e}")

        self.stdout.write(self.style.SUCCESS(f"Successfully logged spend of {amount} for campaign {campaign_id}"))
