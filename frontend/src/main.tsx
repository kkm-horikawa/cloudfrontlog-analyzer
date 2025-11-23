/**
 * @fileoverview アプリケーションのエントリーポイント
 *
 * ReactアプリケーションをDOMにマウントし、StrictModeで実行します。
 * ルート要素にアプリケーションコンポーネントをレンダリングします。
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

/**
 * アプリケーションのルート要素を取得してReactアプリをマウントします
 *
 * - React.StrictModeでアプリケーションをラップし、開発時の警告を有効化
 * - ルート要素が存在しない場合はレンダリングをスキップ
 */
const rootElement = document.getElementById('root');
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
