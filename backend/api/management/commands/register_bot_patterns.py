"""
一般的なボットパターンを登録するDjangoマネジメントコマンド

Usage:
    python manage.py register_bot_patterns
    python manage.py register_bot_patterns --dry-run
"""

from django.core.management.base import BaseCommand

from api.models import LogMarkCategory, LogMarkPattern


# User-Agentベースのボットパターン
USER_AGENT_BOT_PATTERNS = [
    # 検索エンジンボット
    {"pattern": "Googlebot", "note": "Google検索クローラー"},
    {"pattern": "bingbot", "note": "Bing検索クローラー"},
    {"pattern": "Baiduspider", "note": "Baidu検索クローラー"},
    {"pattern": "YandexBot", "note": "Yandex検索クローラー"},
    {"pattern": "DuckDuckBot", "note": "DuckDuckGo検索クローラー"},
    {"pattern": "Slurp", "note": "Yahoo!検索クローラー"},
    {"pattern": "Y!J-BRW", "note": "Yahoo! JAPAN検索クローラー"},
    {"pattern": "Y!J-ASR", "note": "Yahoo! JAPAN検索クローラー (ASR)"},
    {"pattern": "Y!J-BRJ", "note": "Yahoo! JAPAN広告クローラー"},
    {"pattern": "Applebot", "note": "Apple検索クローラー"},
    {"pattern": "GoogleOther", "note": "Google Otherクローラー"},
    {"pattern": "Googlebot-Image", "note": "Google画像検索クローラー"},
    {"pattern": "AdsBot-Google", "note": "Google広告ボット"},
    {"pattern": "Google-Apps-Script", "note": "Google Apps Script"},
    {"pattern": "Google-Read-Aloud", "note": "Google読み上げ機能"},
    {"pattern": "Google-Display-Ads-Bot", "note": "Google Display広告ボット"},
    {"pattern": "Google-InspectionTool", "note": "Google検査ツール"},
    # AIボット
    {"pattern": "ChatGPT-User", "note": "ChatGPT Userボット"},
    {"pattern": "GPTBot", "note": "OpenAI GPTBot"},
    {"pattern": "OAI-SearchBot", "note": "OpenAI SearchBot"},
    {"pattern": "PerplexityBot", "note": "Perplexity AIボット"},
    {"pattern": "Perplexity-User", "note": "Perplexity Userボット"},
    {"pattern": "ClaudeBot", "note": "Anthropic Claudeボット"},
    {"pattern": "Claude-Web", "note": "Anthropic Claude Webクローラー"},
    {"pattern": "ChatGPT/", "note": "ChatGPTアプリ"},
    {"pattern": "cohere-ai", "note": "Cohere AIクローラー"},
    {"pattern": "Google-Extended", "note": "Google AI学習用クローラー"},
    {"pattern": "Gemini", "note": "Google Geminiクローラー"},
    {"pattern": "CCBot", "note": "Common Crawl (AI学習データ収集)"},
    {"pattern": "Diffbot", "note": "Diffbot AIクローラー"},
    {"pattern": "Omgilibot", "note": "Webz.io AIクローラー"},
    {"pattern": "Timpibot", "note": "Timpi AIクローラー"},
    {"pattern": "ImagesiftBot", "note": "Imagesift AIクローラー"},
    {"pattern": "Kangaroo Bot", "note": "Kangaroo AI検索ボット"},
    {"pattern": "YouBot", "note": "You.com AIクローラー"},
    {"pattern": "AI2Bot", "note": "Allen AI研究クローラー"},
    # SNSボット
    {"pattern": "facebookexternalhit", "note": "Facebookクローラー"},
    {"pattern": "Facebot", "note": "Facebookボット"},
    {"pattern": "meta-externalagent", "note": "Meta/Facebookクローラー"},
    {"pattern": "meta-externalads", "note": "Meta/Facebook広告クローラー"},
    {"pattern": "Twitterbot", "note": "Twitterボット"},
    {"pattern": "LinkedInBot", "note": "LinkedInクローラー"},
    {"pattern": "Pinterestbot", "note": "Pinterestクローラー"},
    {"pattern": "Discordbot", "note": "Discordリンクプレビュー"},
    {"pattern": "TelegramBot", "note": "Telegramボット"},
    {"pattern": "Slackbot", "note": "Slackボット"},
    {"pattern": "Slack-ImgProxy", "note": "Slackリンクプレビュー"},
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
    {"pattern": "BLEXBot", "note": "SE Ranking SEOクローラー"},
    {"pattern": "SERankingBacklinksBot", "note": "SE Ranking バックリンクSEOクローラー"},
    # クローラー・スクレイピング
    {"pattern": "Scrapy", "note": "Scrapyフレームワーク"},
    {"pattern": "python-requests", "note": "Python requestsライブラリ"},
    {"pattern": "python-httpx", "note": "Python httpxライブラリ"},
    {"pattern": "aiohttp", "note": "Python aiohttpライブラリ"},
    {"pattern": "curl", "note": "cURLコマンドラインツール"},
    {"pattern": "wget", "note": "wgetコマンドラインツール"},
    {"pattern": "Go-http-client", "note": "Go HTTPクライアント"},
    {"pattern": "okhttp", "note": "OkHttp Androidクライアント"},
    {"pattern": "Java/", "note": "Java HTTPクライアント"},
    {"pattern": "Apache-HttpClient", "note": "Apache HTTPクライアント"},
    {"pattern": "Bytespider", "note": "ByteDance Bytespiderクローラー"},
    {"pattern": "Amazonbot", "note": "Amazon Alexaクローラー"},
    {"pattern": "CriteoBot", "note": "Criteo広告クローラー"},
    {"pattern": "HeadlessChrome", "note": "ヘッドレスChromeブラウザ"},
    # その他のボット
    {"pattern": "IbouBot", "note": "ibou.ioボット"},
    {"pattern": "Cotoyogi", "note": "ROISデータ科学研究センタークローラー"},
    {"pattern": "Flyriverbot", "note": "Flyriverボット"},
    {"pattern": "WPMU DEV", "note": "WPMU DEVリンクチェッカー"},
    {"pattern": "GoogleDocs", "note": "Google Docsスプレッドシート"},
    {"pattern": "TikTokSpider", "note": "TikTokスパイダー"},
    {"pattern": "HubSpot", "note": "HubSpotクローラー"},
    {"pattern": "ShapBot", "note": "Shapボット"},
    {"pattern": "Privacy Preserving Prefetch", "note": "Chromeプリフェッチプロキシ"},
    {"pattern": "GeedoProductSearch", "note": "Geedo商品検索ボット"},
    {"pattern": "adbeat", "note": "Adbeatチェックスクリプト"},
    {"pattern": "ias-", "note": "Integral Ad Science"},
    {"pattern": "AdsTxtCrawler", "note": "ads.txtクローラー"},
    # セキュリティスキャナー
    {"pattern": "Nmap", "note": "Nmapセキュリティスキャナー"},
    {"pattern": "Nikto", "note": "Niktoセキュリティスキャナー"},
    {"pattern": "sqlmap", "note": "sqlmapセキュリティツール"},
    {"pattern": "ZmEu", "note": "ZmEu脆弱性スキャナー"},
    {"pattern": "Palo Alto Networks", "note": "Palo Alto Cortex Xpanseスキャナー"},
    {"pattern": "Censys", "note": "Censysセキュリティスキャナー"},
    {"pattern": "Shodan", "note": "Shodanセキュリティスキャナー"},
    {"pattern": "masscan", "note": "Masscanポートスキャナー"},
    {"pattern": "NetcraftSurveyAgent", "note": "Netcraftセキュリティ調査"},
    {"pattern": "zgrab", "note": "Zmap/Zgrabスキャナー"},
    # 不審・悪意のあるパターン（スクリプト・ツール）
    {"pattern": "libwww-perl", "note": "Perl LWPライブラリ（スクリプト）"},
    {"pattern": "Morfeus", "note": "Morfeusマルウェアスキャナー"},
    {"pattern": "Havij", "note": "Havij SQLインジェクションツール"},
    {"pattern": "WinHttp", "note": "Windows HTTPクライアント（自動化）"},
    {"pattern": "HttpClient", "note": "汎用HTTPクライアント"},
    {"pattern": "fasthttp", "note": "Go fasthttpライブラリ"},
    {"pattern": "axios", "note": "Node.js Axiosライブラリ"},
    {"pattern": "node-fetch", "note": "Node.js fetchライブラリ"},
    {"pattern": "httpx", "note": "HTTPXスキャナー/クライアント"},
    {"pattern": "PycURL", "note": "Python cURLライブラリ"},
    {"pattern": "Nuclei", "note": "Nuclei脆弱性スキャナー"},
    {"pattern": "Acunetix", "note": "Acunetix脆弱性スキャナー"},
    {"pattern": "Nessus", "note": "Nessus脆弱性スキャナー"},
    {"pattern": "Burp", "note": "Burp Suiteセキュリティテスト"},
    {"pattern": "OWASP", "note": "OWASP ZAPセキュリティテスト"},
    {"pattern": "w3af", "note": "w3af脆弱性スキャナー"},
    {"pattern": "Wapiti", "note": "Wapitiセキュリティスキャナー"},
    {"pattern": "Skipfish", "note": "Skipfishセキュリティスキャナー"},
    {"pattern": "Arachni", "note": "Arachniセキュリティスキャナー"},
    {"pattern": "Telerik", "note": "Telerik脆弱性スキャナー"},
    {"pattern": "WebInspect", "note": "HP WebInspectスキャナー"},
    {"pattern": "AppSpider", "note": "AppSpiderスキャナー"},
    {"pattern": "Qualys", "note": "Qualysセキュリティスキャナー"},
]

# 組織ベースのボットパターン
ORGANIZATION_BOT_PATTERNS = [
    {"pattern": "Anthropic", "note": "Anthropic AI (Claude)"},
    {"pattern": "OpenAI", "note": "OpenAI (ChatGPT)"},
    {"pattern": "Perplexity", "note": "Perplexity AI"},
    {"pattern": "Ahrefs", "note": "Ahrefs SEOクローラー"},
    {"pattern": "Criteo", "note": "Criteo広告ボット"},
    {"pattern": "Semrush", "note": "Semrush SEOクローラー"},
    {"pattern": "DataForSEO", "note": "DataForSEO クローラー"},
    {"pattern": "Screaming Frog", "note": "Screaming Frog SEOスパイダー"},
    {"pattern": "MJ12bot", "note": "Majestic SEOクローラー"},
    {"pattern": "ByteDance", "note": "ByteDance (TikTok/Bytespider)"},
    {"pattern": "Palo Alto Networks", "note": "Palo Alto Cortex Xpanseスキャナー"},
    {"pattern": "Cohere", "note": "Cohere AI"},
    {"pattern": "Common Crawl", "note": "Common Crawl (CCBot)"},
    {"pattern": "Diffbot", "note": "Diffbot AI"},
    {"pattern": "Censys", "note": "Censysセキュリティスキャナー"},
    {"pattern": "Shodan", "note": "Shodanセキュリティスキャナー"},
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

        # ボットカテゴリを取得
        try:
            bot_category = LogMarkCategory.objects.get(slug="bot")
        except LogMarkCategory.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Error: 'bot' category not found. Please run migrations first."
                )
            )
            return

        # User-Agentパターンを登録
        ua_registered, ua_skipped = self._register_user_agent_patterns(
            dry_run, bot_category
        )

        # 組織パターンを登録
        org_registered, org_skipped = self._register_organization_patterns(
            dry_run, bot_category
        )

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

    def _register_user_agent_patterns(
        self, dry_run: bool, bot_category: LogMarkCategory
    ):
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
                user_agent_pattern=pattern, category=bot_category
            ).first()

            if existing:
                self.stdout.write(self.style.WARNING(f"[SKIP] Already exists: {pattern}"))
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would register: {pattern} ({note})")
                registered_count += 1
                continue

            # 新規登録
            try:
                LogMarkPattern.objects.create(
                    distribution_id=None,  # 全Distribution対象
                    user_agent_pattern=pattern,
                    match_type="partial",
                    category=bot_category,
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

    def _register_organization_patterns(
        self, dry_run: bool, bot_category: LogMarkCategory
    ):
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
                org_pattern=pattern, category=bot_category
            ).first()

            if existing:
                self.stdout.write(self.style.WARNING(f"[SKIP] Already exists: {pattern}"))
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would register: {pattern} ({note})")
                registered_count += 1
                continue

            # 新規登録
            try:
                LogMarkPattern.objects.create(
                    distribution_id=None,  # 全Distribution対象
                    org_pattern=pattern,
                    match_type="partial",
                    category=bot_category,
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
