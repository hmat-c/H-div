# hmat-assign.pl 使用方法

## 概要
`hmat-assign.pl` は、H行列（階層的行列）の葉行列（リーフ行列）がMPIプロセスやワーカースレッドにどのように割り当てられているかを可視化するPerlスクリプトです。入力ファイルを読み込み、gnuplotを使用してPDFファイルを生成します。

## H行列情報の生成（hmat_array_filling.c）

### コンパイルと実行
```bash
# コンパイル（MKLライブラリが必要）
gcc -o hmat_array_filling hmat_array_filling.c data/bem_file.c -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread -lm

# 実行（-tオプションで可視化用データを生成）
./hmat_array_filling -t [入力ファイル]
```

### 使用例
```bash
# デフォルトの入力ファイルを使用
./hmat_array_filling -t

# 特定の入力ファイルを指定
./hmat_array_filling -t data/input_100ts.txt
```

### 生成されるファイル
実行すると、入力ファイル名に `_hmat` を付加したファイルが生成されます：
- 例：`input_10ts.txt` → `input_10ts.txt_hmat`
- ディレクトリパスは自動的に削除されます

## hmat-assign.pl の基本的な使い方

### 単一ファイルの処理
```bash
perl hmat-assign.pl <inputfile>
```

### 複数プロセスファイルの処理
```bash
perl hmat-assign.pl --mproc <prefix>
```

## オプション

- `--keep, -k`: 実行後もプロットファイルとgnuplotスクリプトを保持する
- `--help, -h`: ヘルプメッセージを表示
- `--mproc=<prefix>, -m <prefix>`: プレフィックスを指定して複数のプロセスファイルを処理
  - `<prefix>0000`, `<prefix>0001`, ... という名前のファイルをすべて読み込む
  - 各ファイルのポストフィックス番号がプロセス番号として扱われる

## 入力ファイルフォーマット

各行は以下の形式で葉行列の情報を記述します：
```
<thr>, <x0>, <y0>, <x1>, <y1>, <mattype>
```

- `<thr>`: スレッド番号（0以上の整数）
- `<x0>, <y0>`: 行列の左上要素のインデックス
- `<x1>, <y1>`: 行列の右下要素のインデックス
- `<mattype>`: 行列タイプ（1: Rk行列、2: 密行列）

## 完全な使用例

### 1. H行列構造の可視化
```bash
# H行列情報ファイルを生成
./hmat_array_filling -t data/input_10ts.txt

# 生成されたファイルを確認
ls input_10ts.txt_hmat

# 可視化PDFを生成
perl hmat-assign.pl input_10ts.txt_hmat

# 生成されたPDFを確認
ls input_10ts.txt_hmat.pdf
```

### 2. 生成ファイルを保持する場合
```bash
perl hmat-assign.pl -k input_10ts.txt_hmat
# input_10ts.txt_hmat-dir/ ディレクトリに中間ファイルが保存される
```

### 3. 複数プロセスの可視化
```bash
# プロセスごとのファイルがある場合（例：hmat_0000, hmat_0001, ...）
perl hmat-assign.pl -m hmat_
```

## 出力

- **PDFファイル**: 入力ファイル名に `.pdf` を付加したファイル（例：`input_10ts.txt_hmat.pdf`）
  - Rk行列：薄い塗りつぶし（透明度0.1）
  - 密行列：濃い塗りつぶし（透明度0.5）
  - スレッドごとに異なる色で表示
  - プロセス境界線も表示（複数プロセスの場合）

- **一時ファイル**（`-k` オプション使用時のみ保持）：
  - プロットファイル：`<inputfile>-dir/thread-<n>-<mattype>.plt`
  - gnuplotスクリプト：`<inputfile>-dir/plot.gnuplot`
  - プロセス境界ファイル：`<inputfile>-dir/boundaries.plt`

## 必要な環境

- Perl
- gnuplot（PDFCairo端末サポート付き）
- MKLライブラリ（hmat_array_fillingのコンパイル時）

## 注意事項

- 入力ファイルと同じディレクトリに出力PDFが生成されます
- 既存のディレクトリがある場合は上書き確認があります
- gnuplotがインストールされていない場合はエラーになります
- hmat_array_fillingの実行時、`-t`オプションを忘れると可視化用ファイルは生成されません