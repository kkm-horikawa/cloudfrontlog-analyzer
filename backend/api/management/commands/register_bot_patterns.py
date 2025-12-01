"""
一般的なボットパターンを登録するDjangoマネジメントコマンド

Usage:
    python manage.py register_bot_patterns
    python manage.py register_bot_patterns --dry-run
"""

from django.core.management.base import BaseCommand

from api.models import LogMarkPattern


# User-Agentベースのボットパターン
USER_AGENT_BOT_PATTERNS = [
    # 検索エンジンボット
    {"pattern": "Googlebot", "note": "Google検索クローラー"},
    {"pattern": "bingbot", "note": "Bing検索クローラー"},
    {"pattern": "Baiduspider", "note": "Baidu検索クローラー"},
    {"pattern": "YandexBot", "note": "Yandex検索クローラー"},
    {"pattern": "DuckDuckBot", "note": "DuckDuckGo検索クローラー"},
    {"pattern": "Slurp", "note": "Yahoo!検索クローラー"},
    # SNSボット
    {"pattern": "facebookexternalhit", "note": "Facebookクローラー"},
    {"pattern": "Twitterbot", "note": "Twitterボット"},
    {"pattern": "LinkedInBot", "note": "LinkedInクローラー"},
    {"pattern": "Pinterestbot", "note": "Pinterestクローラー"},
    {"pattern": "Discordbot", "note": "Discordリンクプレビュー"},
    {"pattern": "TelegramBot", "note": "Telegramボット"},
    {"pattern": "Slackbot", "note": "Slackボット"},
    {"pattern": "WhatsApp", "note": "WhatsAppリンクプレビュー"},
    # モニタリング・アップタイムボット
    {"pattern": "UptimeRobot", "note": "UptimeRobotモニタリング"},
    {"pattern": "Pingdom", "note": "Pingdomモニタリング"},
    {"pattern": "StatusCake", "note": "StatusCakeモニタリング"},
    {"pattern": "NewRelic", "note": "NewRelicモニタリング"},
    {"pattern": "Datadog", "note": "Datadogモニタリング"},
    # SEO・分析ツール
    {"pattern": "AhrefsBot", "note": "Ahrefs SEOクローラー"},
    {"pattern": "SemrushBot", "note": "Semrush SEOクローラー"},
    {"pattern": "MJ12bot", "note": "Majestic SEOクローラー"},
    {"pattern": "DotBot", "note": "Moz SEOクローラー"},
    {"pattern": "SEMrushBot", "note": "SEMrush クローラー"},
    {"pattern": "rogerbot", "note": "Moz SEOボット"},
    # クローラー・スクレイピング
    {"pattern": "Scrapy", "note": "Scrapyフレームワーク"},
    {"pattern": "python-requests", "note": "Python requestsライブラリ"},
    {"pattern": "curl", "note": "cURLコマンドラインツール"},
    {"pattern": "wget", "note": "wgetコマンドラインツール"},
    {"pattern": "Go-http-client", "note": "Go HTTPクライアント"},
    {"pattern": "Java/", "note": "Java HTTPクライアント"},
    {"pattern": "Apache-HttpClient", "note": "Apache HTTPクライアント"},
    # セキュリティスキャナー
    {"pattern": "Nmap", "note": "Nmapセキュリティスキャナー"},
    {"pattern": "Nikto", "note": "Niktoセキュリティスキャナー"},
    {"pattern": "sqlmap", "note": "sqlmapセキュリティツール"},
    {"pattern": "ZmEu", "note": "ZmEu脆弱性スキャナー"},
]

# 組織ベースのボットパターン
ORGANIZATION_BOT_PATTERNS = [
    {"pattern": "Anthropic", "note": "Anthropic AI (Claude)"},
    {"pattern": "OpenAI", "note": "OpenAI (ChatGPT)"},
    {"pattern": "Ahrefs", "note": "Ahrefs SEOクローラー"},
    {"pattern": "Criteo", "note": "Criteo広告ボット"},
    {"pattern": "Semrush", "note": "Semrush SEOクローラー"},
    {"pattern": "DataForSEO", "note": "DataForSEO クローラー"},
    {"pattern": "Screaming Frog", "note": "Screaming Frog SEOスパイダー"},
    {"pattern": "MJ12bot", "note": "Majestic SEOクローラー"},
]


class Command(BaseCommand):
    help = "一般的なボットパターンをLogMarkPatternに登録します"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="実際には登録せず、登録される内容を表示するだけ",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        self.stdout.write("=" * 80)
        self.stdout.write("Common Bot Pattern Registration")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Dry run: {dry_run}\n")

        # User-Agentパターンを登録
        ua_registered, ua_skipped = self._register_user_agent_patterns(dry_run)

        # 組織パターンを登録
        org_registered, org_skipped = self._register_organization_patterns(dry_run)

        # 最終結果
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Registration Summary")
        self.stdout.write("=" * 80)
        self.stdout.write(
            f"User-Agent patterns: {ua_registered} registered, {ua_skipped} skipped"
        )
        self.stdout.write(
            f"Organization patterns: {org_registered} registered, {org_skipped} skipped"
        )
        self.stdout.write(
            f"Total: {ua_registered + org_registered} registered, {ua_skipped + org_skipped} skipped"
        )
        self.stdout.write("=" * 80)

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Successfully registered {ua_registered + org_registered} bot patterns"
                )
            )

    def _register_user_agent_patterns(self, dry_run: bool):
        """User-Agentベースのボットパターンを登録"""
        self.stdout.write("=" * 80)
        self.stdout.write("Registering User-Agent based bot patterns")
        self.stdout.write("=" * 80)

        registered_count = 0
        skipped_count = 0

        for bot_info in USER_AGENT_BOT_PATTERNS:
            pattern = bot_info["pattern"]
            note = bot_info["note"]

            # 既存のパターンをチェック
            existing = LogMarkPattern.objects.filter(
                user_agent_pattern=pattern, mark_type="bot"
            ).first()

            if existing:
                self.stdout.write(self.style.WARNING(f"[SKIP] Already exists: {pattern}"))
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would register: {pattern} ({note})")
                continue

            # 新規登録
            try:
                LogMarkPattern.objects.create(
                    distribution_id=None,  # 全Distribution対象
                    user_agent_pattern=pattern,
                    match_type="partial",
                    mark_type="bot",
                    note=note,
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[REGISTERED] {pattern} - {note}")
                )
                registered_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] Failed to register {pattern}: {e}")
                )

        self.stdout.write(
            f"\nUser-Agent patterns: {registered_count} registered, {skipped_count} skipped"
        )
        return registered_count, skipped_count

    def _register_organization_patterns(self, dry_run: bool):
        """組織ベースのボットパターンを登録"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("Registering Organization based bot patterns")
        self.stdout.write("=" * 80)

        registered_count = 0
        skipped_count = 0

        for bot_info in ORGANIZATION_BOT_PATTERNS:
            pattern = bot_info["pattern"]
            note = bot_info["note"]

            # 既存のパターンをチェック
            existing = LogMarkPattern.objects.filter(
                org_pattern=pattern, mark_type="bot"
            ).first()

            if existing:
                self.stdout.write(self.style.WARNING(f"[SKIP] Already exists: {pattern}"))
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would register: {pattern} ({note})")
                continue

            # 新規登録
            try:
                LogMarkPattern.objects.create(
                    distribution_id=None,  # 全Distribution対象
                    org_pattern=pattern,
                    match_type="partial",
                    mark_type="bot",
                    note=note,
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[REGISTERED] {pattern} - {note}")
                )
                registered_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] Failed to register {pattern}: {e}")
                )

        self.stdout.write(
            f"\nOrganization patterns: {registered_count} registered, {skipped_count} skipped"
        )
        return registered_count, skipped_count
