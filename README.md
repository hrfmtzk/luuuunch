# Luuuunch for Google Chat

昼休憩を連絡するためのチャットボットです。

メンバーとして登録されたルームに対して平日 12:00 (JST) に連絡用のカードメッセージを投稿します。

## 1. Deployment

HTTP エンドポイントタイプのチャットボットを作成します。

### 1.1. 事前準備

- API Gateway に割り当てるカスタムドメイン及び ACM 証明書

### 1.2. GCP でのボット設定

1. [サービスアカウントの使用](https://developers.google.com/chat/how-tos/service-accounts) を参考に JSON 形式のクレデンシャル情報を取得します
   - この情報は 1.3. の手順の中で利用します
1. [ボットの公開](https://developers.google.com/chat/how-tos/bots-publish) を参考にボットの公開設定を行います
   - 設定は以下のように行います
     - **Bot name** - {任意} (e.g. `Luuuunch`)
     - **Avatar URL** - {任意} (e.g. `https://github.com/hrfmtzk/luuuunch/blob/main/assets/luuuunch.png?raw=true`)
     - **Connection settins**
       - **Bot URL** - `https://{カスタムドメイン}/api/callback`

### 1.3. AWS へのボットデプロイ

1. `.env` 等に必要な環境変数を設定した状態で CDK アプリケーションのデプロイを実施する
1. 作成された Secrets Manager に 1.2. で作成した JSON 形式のクレデンシャルを保存する

#### 環境変数

- **CERTIFICATE_ARN**
  - カスタムドメイン用 ACM 証明書の ARN
  - 必須 - yes
- **DOMAIN_NAME**
  - カスタムドメイン用 ドメイン名
  - 必須 - yes
- **ICON_URL**
  - カードメッセージヘッダ用画像 URL
  - 必須 - yes
- **PROJECT_ID**
  - ボットプロジェクト ID (ボットの公開にて発行されたもの)
- **REPLY_MESSAGE**
  - ボットにメッセージを送った際の応答文
  - 必須 - no
- **LOG_LEVEL**
  - Lambda Function に設定されたロガーのログレベル
  - 必須 - no
  - デフォルト - `INFO`
- **SENTRY_DSN**
  - Lambda Function に設定された Sentry クライアント用 DSN
  - 必須 - no
