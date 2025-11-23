/**
 * @fileoverview Viteビルドツールの設定ファイル
 *
 * React + TypeScript + Tailwind CSSプロジェクトのビルド設定を定義します。
 * 開発サーバーの設定とHMR（Hot Module Replacement）の設定を含みます。
 *
 * 主な設定:
 * - Reactプラグイン: JSX/TSXサポート
 * - Tailwind CSSプラグイン: スタイリングサポート
 * - 開発サーバー: 0.0.0.0:5173でホスト、ポーリングによるファイル監視
 * - HMR: localhostでホットリロード
 *
 * @see {@link https://vitejs.dev/config/}
 */

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

/**
 * Vite設定オブジェクト
 *
 * プラグインと開発サーバーの設定を定義します。
 */
export default defineConfig({
  /** 使用するViteプラグインの配列 */
  plugins: [react(), tailwindcss()],

  /** 開発サーバーの設定 */
  server: {
    /** すべてのネットワークインターフェースでリッスン */
    host: '0.0.0.0',
    /** ポート番号 */
    port: 5173,
    /** ファイル監視の設定 */
    watch: {
      /** ポーリングを使用してファイル変更を検出（Docker環境で推奨） */
      usePolling: true,
    },
    /** HMR（Hot Module Replacement）の設定 */
    hmr: {
      /** HMRのホスト名 */
      host: 'localhost',
    },
  },
});
