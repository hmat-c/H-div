# BEM データ処理ツール群

このディレクトリには、BEM（境界要素法）データを処理・操作するためのCプログラム群と、付属の可視化ツールが含まれています。

## 概要

BEMデータファイルの生成、変換、処理を行うCプログラムを中心に、データの可視化を支援するPythonツールを提供しています。これらのツールは、3次元境界要素法解析で使用されるメッシュデータの取り扱いを効率化します。

## メインプログラム（C言語）

### プログラム構成

#### 1. bem_convert
BEMデータファイルのフォーマット変換を行うプログラムです。
- テキスト形式、バイナリ形式、VTK形式、整形表示形式間の相互変換
- 大規模データの効率的な処理
- 様々な解析ソフトウェアとの互換性確保

#### 2. bem_generate
既存のBEMオブジェクトを複製・配置して新しいBEMデータファイルを生成するプログラムです。
- **ピラミッド配置（pコマンド）**: 1+4+9+...+n²個のオブジェクトをピラミッド状に配置
- **直方体配置（cコマンド）**: nx×ny×nz個のオブジェクトを直方体状に配置
- 距離パラメータは隣接するオブジェクトの中心間距離をオブジェクトの直径に対する比率で指定
  - 1.0: オブジェクトが接触
  - 1.5: オブジェクト間に直径の0.5倍の隙間
  - 2.0: オブジェクト間に直径の1.0倍の隙間
- 出力ファイル名を省略すると、コマンドパラメータから自動生成

### ビルド方法

```bash
cd data/
make
```

これにより、`bem_convert`と`bem_generate`の実行ファイルが生成されます。

### 使用例

フォーマット変換：
```bash
./bem_convert -i input.txt -o output.vtk -f vtk
```

メッシュ生成（ピラミッド配置）：
```bash
./bem_generate p 1.5 3 base_input.txt output.txt
```

メッシュ生成（直方体配置）：
```bash
./bem_generate c 1.2 4 4 4 base_input.txt output.txt
```

### ソースファイル構成
- **bem_file.h/c**: BEMファイルの読み書き機能の実装
  - 各種フォーマットのパーサー
  - データ構造の定義
- **bem_aux.c**: 補助関数群
  - 時間計測機能
  - ファイル入出力支援
- **bem_convert.c**: フォーマット変換プログラムのメイン
- **bem_generate.c**: データ生成プログラムのメイン
- **filling.h/c**: 行列要素の充填に関する処理

## ライブラリとしての使用方法

`bem_file.h/c`は、BEMデータファイルを読み込むためのライブラリとして他のプログラムから利用できます。

### 基本的な使い方

```c
#include <stdio.h>
#include <stdlib.h>
#include "data/bem_file.h"

int main(int argc, char **argv) {
    const char *filename = "input_data.txt";
    FILE *file;
    struct bem_input bi;
    
    // ファイルを開く
    file = fopen(filename, "r");
    if (file == NULL) {
        fprintf(stderr, "Error: Unable to open file '%s'\n", filename);
        exit(1);
    }
    
    // BEMデータを読み込む
    if (read_bem_input(file, &bi, BI_AUTO) == -1) {
        fprintf(stderr, "BEM input file read error!\n");
        fclose(file);
        exit(1);
    }
    fclose(file);
    
    // 読み込んだデータにアクセス
    printf("Number of nodes: %ld\n", bi.nNode);
    printf("Number of faces: %ld\n", bi.nFace);
    
    // 頂点座標にアクセス
    for (int i = 0; i < bi.nNode; i++) {
        printf("Node %d: (%f, %f, %f)\n", i,
               bi.coordOfNode[i][0],
               bi.coordOfNode[i][1],
               bi.coordOfNode[i][2]);
    }
    
    // 面の中心座標にアクセス
    for (int i = 0; i < bi.nFace; i++) {
        printf("Face %d center: (%f, %f, %f)\n", i,
               bi.coordOfFace[i][0],
               bi.coordOfFace[i][1],
               bi.coordOfFace[i][2]);
    }
    
    // 面を構成する頂点インデックスにアクセス
    for (int i = 0; i < bi.nFace; i++) {
        printf("Face %d vertices: %d, %d, %d\n", i,
               bi.face2node[i][0],
               bi.face2node[i][1],
               bi.face2node[i][2]);
    }
    
    return 0;
}
```

### コンパイル方法

```bash
gcc -o myprogram myprogram.c data/bem_file.c data/bem_aux.c -lm
```

### 利用可能な関数

#### read_bem_input
```c
enum bi_format read_bem_input(FILE* fp, struct bem_input* pbin, enum bi_format fmt);
```
- ファイルポインタからBEMデータを読み込む
- `fmt`に`BI_AUTO`を指定すると自動的にフォーマットを判別
- 成功時は読み込んだフォーマットを返し、失敗時は-1を返す

#### open_and_read_bem_input
```c
enum bi_format open_and_read_bem_input(char *ifile, struct bem_input* pbin, enum bi_format fmt);
```
- ファイル名を指定してBEMデータを読み込む（ファイルの開閉も行う）

#### print_bem_input
```c
void print_bem_input(FILE* fp, struct bem_input* pbin, enum bi_format fmt);
```
- BEMデータを指定されたフォーマットで出力

### bem_input構造体のフィールド

- `nNode`: 頂点数
- `coordOfNode`: 頂点座標の配列 `[nNode][3]`
- `nFace`: 面の数
- `coordOfFace`: 面の中心座標の配列 `[nFace][3]`
- `face2node`: 各面を構成する頂点インデックスの配列 `[nFace][3]`
- その他のフィールドについては`bem_file.h`を参照

### 実装例：hmat_array_filling.c

実際の使用例として、`hmat_array_filling.c`では以下のようにライブラリを使用しています：

```c
#include "data/bem_file.h"

struct bem_input bi;
file = fopen(fname, "r");
if (read_bem_input(file, &bi, BI_AUTO) == -1) {
    fprintf(stderr, "Bem input file read error!\n");
    exit(99);
}
fclose(file);

// データを変数に格納
countOfNode = bi.nNode;
bgmid = bi.coordOfNode;
count = bi.nFace;
zgmid = bi.coordOfFace;
f2n = bi.face2node;
```

## データフォーマット

### BEMデータファイルフォーマット

BEMデータファイルは**テキスト形式**と**バイナリ形式**の2種類をサポートしています。

#### テキスト形式

データファイルは以下の構造を持つテキストファイルです：

```
<頂点数>
<頂点0のX座標> <頂点0のY座標> <頂点0のZ座標>
<頂点1のX座標> <頂点1のY座標> <頂点1のZ座標>
...
<面の数>
3
0
0
<面0の頂点インデックス0> <面0の頂点インデックス1> <面0の頂点インデックス2>
<面1の頂点インデックス0> <面1の頂点インデックス1> <面1の頂点インデックス2>
...
```

#### バイナリ形式

バイナリ形式は高速な読み書きと小さなファイルサイズを実現します。

**バイナリフォーマット構造：**

```
"BI_BINARY\n"                    # プリアンブル（ASCII文字列）
int64_t: nNode                   # 頂点数
double[nNode][3]: coordOfNode    # 頂点座標 (x,y,z)
int64_t: nFace                   # 面の数
int64_t: nNodePerFace            # 面ごとの頂点数（常に3）
int64_t: nIFValue                # 面ごとの整数パラメータ数
int64_t: nDFValue                # 面ごとの実数パラメータ数
int64_t[nFace][3]: idOfFace      # 面を構成する頂点インデックス
double[nFace][3]: coordOfFace    # 面の中心座標
int[nFace][3]: face2node         # 面を構成する頂点インデックス（int32）
int64_t[nFace][nIFValue]: IFValue    # 整数パラメータ（存在する場合）
double[nFace][nDFValue]: DFValue      # 実数パラメータ（存在する場合）
```

**データ型：**
- `int64_t`: 8バイト整数（リトルエンディアン）
- `int`: 4バイト整数（リトルエンディアン）
- `double`: 8バイト浮動小数点（IEEE 754、リトルエンディアン）

#### フォーマット変換

`bem_convert`を使用してテキスト形式とバイナリ形式を相互変換できます：

```bash
# テキストからバイナリへ変換
./bem_convert -o output_filename -b input.txt

# バイナリからテキストへ変換
./bem_convert -o output_filename -t input.bin

# 自動判定（拡張子で出力形式を決定）
./bem_convert input.txt    # → input.bin を生成
./bem_convert input.bin    # → input.txt を生成
```

## 付属ツール（Python）

### 3Dポリゴンデータ可視化ツール

BEMデータの視覚的な確認を支援するPythonツールです。

#### visualize_polygon.py
高度な機能を持つ3D可視化プログラムです。
- **基本的な3D表示**: マウスによる視点操作
- **透明度調整**: スライダーでポリゴンの透明度を調整
- **エッジ幅調整**: スライダーでエッジの太さを調整
- **頂点表示**: ボタンで頂点の表示/非表示を切り替え
- **軽量モード**: ボタンで三角形の重心のみを点で表示する軽量モードに切り替え（大規模データの高速表示）
- **適応的点サイズ**: 軽量モードで点の密度に応じて自動的にサイズを調整（重なりを防ぐ）
- **画像ファイル出力**: GUIを表示せずに画像ファイルとして保存（バッチ処理対応）
- **ベクター形式対応**: PDF・SVG形式での高品質なベクター画像出力
- **自動ファイルサイズ制御**: ベクターファイルが大きくなりすぎる場合の自動PNG切り替え
- **視点設定**: 仰角・方位角を指定して任意の視点から表示
- **高解像度出力**: DPIを指定して高品質な画像を生成
- **シェーディング**: 簡易的な光源計算による陰影表現
- **統計情報表示**: 表面積、重心などの情報を表示
- **リセット機能**: 設定を初期状態に戻す
- **自動的な軸範囲設定**: データに合わせて軸範囲を自動調整
- **バイナリ形式対応**: 高速読み込みのためのバイナリ形式（.bin）をサポート

### Python環境の準備

```bash
pip install numpy matplotlib
```

### 可視化ツールの使用方法

基本的な使用方法：
```bash
python3 visualize_polygon.py input_10ts.txt
```

コマンドラインオプション：
```bash
python3 visualize_polygon.py [オプション] [ファイル名]

オプション:
  -h, --help            ヘルプメッセージを表示
  --alpha ALPHA, -a ALPHA
                        ポリゴンの透明度（0.1-1.0、デフォルト: 0.8）
  --edge-width WIDTH, -e WIDTH
                        エッジの幅（0.0-1.0、デフォルト: 0.1）
  --show-vertices, -v   起動時に頂点を表示
  --lightweight, -l     軽量モード（三角形の重心のみ表示）で起動
  --output FILE, -o FILE
                        画像ファイルとして保存（GUIを表示しない）
                        拡張子でフォーマット決定（.pdf, .svg, .png等）
                        拡張子なしの場合はPDF形式
  --dpi DPI, -d DPI     出力画像のDPI（デフォルト: 150）
  --elev ANGLE          視点の仰角（デフォルト: 20）
  --azim ANGLE          視点の方位角（デフォルト: 30）
  --point-size SIZE, -p SIZE
                        軽量モードでの点のサイズ（指定しない場合は密度に応じて自動調整）
  --max-vector-size SIZE
                        ベクター形式の最大ファイルサイズ（MB、デフォルト: 5）
                        これを超える場合は自動的にPNGに切り替え
```

使用例：
```bash
# 透明度を0.5、エッジ幅を0.2に設定
python3 visualize_polygon.py --alpha 0.5 --edge-width 0.2 input.txt

# 軽量モードで起動し、頂点も表示
python3 visualize_polygon.py -l -v input.txt

# すべてのオプションを使用
python3 visualize_polygon.py -a 0.6 -e 0.05 -v -l large_data.txt

# 画像ファイルとして保存（GUIなし）
python3 visualize_polygon.py -o output.png input.txt

# 高解像度画像を特定の視点から生成
python3 visualize_polygon.py -o visualization.png --dpi 300 --elev 30 --azim 60 input.txt

# 軽量モードで画像を生成（大規模データ用）
python3 visualize_polygon.py -l -o lightweight_view.png --dpi 200 large_data.txt

# 軽量モードで点のサイズを手動指定
python3 visualize_polygon.py -l -p 1.5 -o small_points.png dense_data.txt

# ベクター形式（PDF）で保存
python3 visualize_polygon.py -o output.pdf input.txt

# ベクター形式（SVG）で保存
python3 visualize_polygon.py -o output.svg input.txt

# 拡張子なし（デフォルトでPDF）
python3 visualize_polygon.py -o output input.txt

# ベクターファイルサイズ制限を10MBに変更
python3 visualize_polygon.py -o large_output.pdf --max-vector-size 10 input.txt

# バイナリファイルを可視化（自動判定）
python3 visualize_polygon.py input_196kp26.bin

# バイナリファイルを軽量モードで高速可視化
python3 visualize_polygon.py -l -o binary_vis.png input_2ms.bin
```

### 操作方法

#### マウス操作
- **左ドラッグ**: 視点の回転
- **右ドラッグ**: ズーム
- **中ドラッグ**: パン（移動）

#### キーボード操作（Matplotlib標準）
- **s**: 現在の表示を画像として保存
- **q**: アプリケーションを終了

## 必要な環境

### Cプログラム
- GCCコンパイラ（C99対応）
- Make

### Python可視化ツール
- Python 3.6以上
- NumPy
- Matplotlib

## サンプルデータセット

`bem_bb_inputs`ディレクトリには、様々な規模のBEMデータファイルが含まれています：

### データセット概要
- **総ファイル数**: 49個のBEMデータファイル
- **規模範囲**: 26面～50,000,000面（6桁の範囲）
- **用途**: アルゴリズムのベンチマーク、スケーラビリティテスト

### 規模別分類
| 分類 | 面数範囲 | 代表例 | 用途 |
|------|----------|--------|------|
| 小規模 | 26-29面 | input2.txt, input3.txt | 基本動作確認 |
| 中規模 | 600-338,000面 | input_10ts.txt, input_338ts.txt | 一般的な解析 |
| 大規模 | 648,000-1,965,600面 | input_1ms.txt, input_196kp26.txt | 高精度解析 |
| 超大規模 | 2,000,000-50,000,000面 | input_2ms.txt, input_50ms.txt | 大規模並列計算 |

### 推奨可視化方法
- **小規模・中規模**: 通常モード（全三角形表示）
- **大規模・超大規模**: 軽量モード（重心点表示）推奨

## 出力される情報

プログラム実行時に以下の情報がコンソールに表示されます：
- 座標数
- 面の数
- 頂点データの形状
- 座標の範囲（X, Y, Z）
- 総表面積
- 重心座標

## トラブルシューティング

### Cプログラムのコンパイルエラー
- GCCのバージョンを確認してください（gcc --version）
- C99標準に対応している必要があります

### Python関連のエラー

#### エラー: "No module named 'numpy'"
NumPyがインストールされていません。以下のコマンドでインストールしてください：
```bash
pip install numpy
```

#### エラー: "No module named 'matplotlib'"
Matplotlibがインストールされていません。以下のコマンドでインストールしてください：
```bash
pip install matplotlib
```

#### 表示されない、または表示が遅い
- 大規模なデータの場合、描画に時間がかかることがあります
- グラフィックドライバが最新であることを確認してください
- SSH経由で実行している場合は、X11転送が有効になっていることを確認してください

#### 軽量モードで点がベタ塗りに見える
- 点のサイズが大きすぎる可能性があります。`-p`オプションで小さな値（0.1-1.0）を指定してください
- 超大規模データ（100万面以上）では点密度が非常に高くなります
- ベクター形式（PDF/SVG）で出力し、拡大表示することで個々の点を確認できます

#### ベクター形式の出力が遅い、またはファイルが巨大になる
- 大規模データではベクター形式のファイルサイズが非常に大きくなります
- `--max-vector-size`オプションでサイズ制限を設定すると、自動的にPNGに切り替わります
- 軽量モードを使用することでベクターファイルサイズを削減できます

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 作者

BEMデータ処理ツールおよび3Dポリゴンデータ可視化ツール開発チーム

## 更新履歴

- 2025-08-25:
  - バイナリフォーマットのサポートを追加
  - visualize_polygon.pyがバイナリファイル（.bin）を直接読み込み可能に
  - バイナリフォーマットの詳細仕様をドキュメントに追加
- 2025-08-24:
  - ベクター形式（PDF・SVG）での画像出力機能を追加
  - 自動ファイルサイズ制御機能を追加（ベクターファイルが指定サイズを超える場合の自動PNG切り替え）
  - デフォルト視点角度を調整（方位角を45度から30度に変更）
- 2025-08-23: 
  - visualize_polygon_advanced.pyをvisualize_polygon.pyに統合、ドキュメントを更新
  - 軽量モード（三角形の重心のみを表示）を追加
  - コマンドラインオプションを追加（透明度、エッジ幅、頂点表示、軽量モードの初期設定）
  - 画像ファイル出力機能を追加（GUIなしでの画像生成、DPI設定、視点角度設定）
  - 適応的点サイズ機能を追加（点の密度に応じて自動的にサイズを調整し、重なりを防ぐ）
- 2025-08-20: Cプログラム群の説明を追加、README構成を再編
- 2025-08-19: 初版リリース
  - 基本的な可視化機能
  - 高度な可視化機能（スライダー、ボタン付き）