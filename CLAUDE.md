# このリポジトリでの振る舞い

吉田さん（究極RIDE／吉田塾）の業務情報を Gmail・Wix から集めて管理するリポジトリ。
質問には**結論を先に、短く**答える。まずこのリポジトリのファイルを読み、足りなければGmail/Wixを確認する。

## ファイルと質問の対応

| 質問の種類 | 見るファイル |
|---|---|
| 今やること・全体 | README.md |
| プリント職人への発注・枚数・金額 | 01_プリント職人_発注.md, data/プリント職人_発注一覧.csv |
| お客様のTシャツ購入・発送 | 02_Tシャツ_注文.md |
| 吉田塾の予約・参加者・キャンセル | 03_吉田塾_予約.md, data/吉田塾_予約一覧.csv（`python3 scripts/juku.py <日付/名前>`） |
| YouTube案件・料金表 | 04_YouTube案件.md |
| 弁護士・訴訟 | 05_弁護士.md |

## 「更新して」と言われたら

1. **プリント職人**: Gmail `from:tranpacjapan.com newer_than:<前回更新から>`。「リピート注文を承りました」に色・サイズ・枚数、「ご注文確定のお知らせ」に金額・出荷日、「出荷案内」で出荷済み
2. **Tシャツ注文**: Gmail `(subject:Tシャツ OR subject:8の字) -from:tranpacjapan.com -category:promotions`
3. **吉田塾**: Wix site `89b15688-1d63-435b-9d60-5781519afb1c` の Query Extended Bookings
   (`https://www.wixapis.com/_api/bookings-reader/v2/extended-bookings/query`, filter `booking.createdDate >= 2026-01-01`, cursorPaging 100)。
   Gmailの「新しい予約があります」は開催日が `${start_date}` と壊れているため使わない
4. **YouTube案件**: Gmail で コラボ/案件/タイアップ/PR（宣伝メールは除外）
5. **弁護士**: Gmail `from:aratana.org OR from:oumilaw.jp`
6. 各ファイルの「最終更新」日付と README の「今すぐやること」を更新してコミット

## ルール

- お客様のメール・電話番号・住所はファイルに書かない（氏名のみ）
- 状態の表記: 吉田塾＝確定／仮予約／キャンセル、発注＝納品済／決済待ち など
