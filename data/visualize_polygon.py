#!/usr/bin/env python3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import sys
import argparse
from matplotlib.widgets import Slider, Button
import matplotlib.colors as mcolors
import struct

def read_polygon_data(filename):
    """ポリゴンデータを読み込む関数（テキストまたはバイナリ形式）"""
    # ファイルの拡張子でフォーマットを判定
    if filename.endswith('.bin'):
        return read_polygon_data_binary(filename)
    else:
        return read_polygon_data_text(filename)

def read_polygon_data_binary(filename):
    """バイナリ形式のポリゴンデータを読み込む関数"""
    with open(filename, 'rb') as f:
        # プリアンブルをチェック
        preamble = f.readline().decode('ascii').strip()
        if preamble != 'BI_BINARY':
            raise ValueError(f"Invalid binary file format: {preamble}")
        
        # 座標数を読み込む（int64_t）
        n_vertices = np.fromfile(f, dtype=np.int64, count=1)[0]
        print(f"座標数: {n_vertices}")
        
        # 座標データを読み込む（double * 3 * n_vertices）
        vertices = np.fromfile(f, dtype=np.float64, count=n_vertices * 3).reshape(n_vertices, 3)
        
        # 面の数を読み込む（int64_t）
        n_faces = np.fromfile(f, dtype=np.int64, count=1)[0]
        print(f"面の数: {n_faces}")
        
        # 面ごとの頂点数（int64_t）
        n_nodes_per_face = np.fromfile(f, dtype=np.int64, count=1)[0]
        if n_nodes_per_face != 3:
            raise ValueError(f"Only triangular faces are supported, got {n_nodes_per_face}")
        
        # 面ごとのintパラメータ数（int64_t）
        n_if_value = np.fromfile(f, dtype=np.int64, count=1)[0]
        
        # 面ごとのdoubleパラメータ数（int64_t）
        n_df_value = np.fromfile(f, dtype=np.int64, count=1)[0]
        
        # 面データを読み込む（int64_t * 3 * n_faces）
        faces = np.fromfile(f, dtype=np.int64, count=n_faces * 3).reshape(n_faces, 3)
        
        # 面の中心座標を読み込む（double * 3 * n_faces）
        # これは可視化には不要なのでスキップ
        f.seek(8 * 3 * n_faces, 1)  # 1 = SEEK_CUR
        
        # face2nodeデータを読み込む（int * 3 * n_faces）
        # これも可視化には不要なのでスキップ
        f.seek(4 * 3 * n_faces, 1)
        
        # IFValueとDFValueがある場合はスキップ
        if n_if_value > 0:
            f.seek(8 * n_if_value * n_faces, 1)
        if n_df_value > 0:
            f.seek(8 * n_df_value * n_faces, 1)
    
    return vertices, faces

def read_polygon_data_text(filename):
    """テキスト形式のポリゴンデータを読み込む関数"""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # 座標数を読み込む
    n_vertices = int(lines[0].strip())
    print(f"座標数: {n_vertices}")
    
    # 座標データを読み込む
    vertices = []
    for i in range(1, n_vertices + 1):
        coords = lines[i].strip().split()
        x, y, z = float(coords[0]), float(coords[1]), float(coords[2])
        vertices.append([x, y, z])
    vertices = np.array(vertices)
    
    # 面の数を読み込む
    face_count_line = n_vertices + 1
    n_faces = int(lines[face_count_line].strip())
    print(f"面の数: {n_faces}")
    
    # 無視する行をスキップ（3行）
    start_face_data = face_count_line + 4
    
    # 面データを読み込む
    faces = []
    for i in range(start_face_data, start_face_data + n_faces):
        face_data = lines[i].strip().split()
        # 各面は3つの頂点インデックスを持つ
        v1, v2, v3 = int(face_data[0]), int(face_data[1]), int(face_data[2])
        # 1-based indexingの場合は0-basedに変換
        max_index = max(v1, v2, v3)
        if max_index >= n_vertices:
            # 1-based indexing detected
            v1, v2, v3 = v1 - 1, v2 - 1, v3 - 1
        faces.append([v1, v2, v3])
    
    return vertices, faces

def calculate_face_normals(vertices, faces):
    """各面の法線ベクトルを計算"""
    normals = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        # 2つのエッジベクトルを計算
        edge1 = v1 - v0
        edge2 = v2 - v0
        # 外積で法線を計算
        normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
        normals.append(normal)
    return np.array(normals)

def calculate_face_centroids(vertices, faces):
    """各三角形面の重心を計算"""
    centroids = []
    for face in faces:
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        # 三角形の重心は3頂点の平均
        centroid = (v0 + v1 + v2) / 3.0
        centroids.append(centroid)
    return np.array(centroids)

def calculate_adaptive_point_size(centroids, base_size=3, min_size=0.5, max_size=10):
    """重心点の密度に基づいて適応的な点サイズを計算"""
    if len(centroids) < 2:
        return base_size
    
    # 最近傍点までの平均距離を計算（サンプリングして高速化）
    n_samples = min(1000, len(centroids))
    if len(centroids) > n_samples:
        # ランダムサンプリング
        indices = np.random.choice(len(centroids), n_samples, replace=False)
        sample_centroids = centroids[indices]
    else:
        sample_centroids = centroids
    
    # 各点から最近傍点までの距離を計算
    min_distances = []
    for i in range(len(sample_centroids)):
        # 自分自身以外の点との距離
        distances = np.linalg.norm(sample_centroids - sample_centroids[i], axis=1)
        distances[i] = np.inf  # 自分自身を除外
        if len(distances) > 1:
            min_distances.append(np.min(distances))
    
    if min_distances:
        # 平均最近傍距離に基づいてサイズを調整
        avg_min_distance = np.mean(min_distances)
        
        # データの全体的なスケールを考慮
        data_range = np.max(centroids) - np.min(centroids)
        relative_density = avg_min_distance / data_range if data_range > 0 else 0.01
        
        # 密度に基づいてサイズを計算（密度が高いほど小さく）
        # relative_densityが小さい（密）ほど、点を小さくする
        size = base_size * (relative_density * 100)
        size = np.clip(size, min_size, max_size)
        
        return size
    
    return base_size

def visualize_polygon_noninteractive(vertices, faces, output_file, dpi=150, 
                                   elev=20, azim=30, title="3D Polygon Visualization",
                                   initial_alpha=0.8, initial_edge_width=0.1,
                                   show_vertices=False, lightweight_mode=False, 
                                   manual_point_size=None, max_vector_size_mb=5):
    """非インタラクティブモードで3Dポリゴンを画像ファイルとして保存"""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 法線ベクトルを計算（シェーディング用）
    normals = calculate_face_normals(vertices, faces)
    
    # 三角形の重心を計算
    centroids = calculate_face_centroids(vertices, faces)
    
    if lightweight_mode:
        # 軽量モード: 重心のみ表示
        # 密度に基づいて点のサイズを自動調整（手動指定がない場合）
        if manual_point_size is not None:
            point_size = manual_point_size
        else:
            point_size = calculate_adaptive_point_size(centroids)
        ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2], 
                  c='blue', s=point_size, alpha=0.6)
        ax.set_title(title + f" (Lightweight Mode, point size={point_size:.1f})")
    else:
        # 通常モード: ポリゴン表示
        # 光源の方向（簡易的なシェーディング）
        light_dir = np.array([1, 1, 1])
        light_dir = light_dir / np.linalg.norm(light_dir)
        
        # ポリゴンのコレクションを作成
        poly3d = []
        face_colors = []
        
        for i, face in enumerate(faces):
            # 各面の頂点座標を取得
            triangle = vertices[face]
            poly3d.append(triangle)
            
            # 簡易的なシェーディング（法線と光源の内積）
            shade = max(0.3, min(1.0, np.dot(normals[i], light_dir) * 0.7 + 0.5))
            face_colors.append((0, shade, shade))  # シアン系の色でシェーディング
        
        # ポリゴンコレクションを追加
        poly_collection = Poly3DCollection(poly3d, alpha=initial_alpha, 
                                         facecolors=face_colors,
                                         edgecolor='black', linewidth=initial_edge_width)
        ax.add_collection3d(poly_collection)
        ax.set_title(title)
    
    # 頂点表示（軽量モードでは表示しない）
    if show_vertices and not lightweight_mode:
        ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
                  c='red', s=1, alpha=0.5)
    
    # 軸の範囲を設定（等縮尺）
    x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()
    y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
    z_min, z_max = vertices[:, 2].min(), vertices[:, 2].max()
    
    # 最大範囲を計算
    x_range = x_max - x_min
    y_range = y_max - y_min
    z_range = z_max - z_min
    max_range = max(x_range, y_range, z_range)
    
    # 各軸の中心を計算
    x_center = (x_max + x_min) / 2
    y_center = (y_max + y_min) / 2
    z_center = (z_max + z_min) / 2
    
    # 等縮尺で軸範囲を設定（1.1倍のマージンを追加）
    half_range = max_range * 1.1 / 2
    ax.set_xlim(x_center - half_range, x_center + half_range)
    ax.set_ylim(y_center - half_range, y_center + half_range)
    ax.set_zlim(z_center - half_range, z_center + half_range)
    
    # ラベルとグリッド
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.grid(True)
    
    # 視点を設定
    ax.view_init(elev=elev, azim=azim)
    
    # 画像として保存
    # ファイル拡張子に基づいてフォーマットを決定
    file_ext = output_file.lower().split('.')[-1] if '.' in output_file else 'pdf'
    original_ext = file_ext
    
    if file_ext in ['pdf', 'svg']:
        # ベクター形式のサイズを推定
        # 面数に基づく概算（経験的な値）
        estimated_size_mb = len(faces) * 0.001 if not lightweight_mode else len(centroids) * 0.0005
        
        if estimated_size_mb > max_vector_size_mb:
            # サイズが大きすぎる場合はPNGに自動切り替え
            if '.' in output_file:
                output_file = output_file.rsplit('.', 1)[0] + '.png'
            else:
                output_file = output_file + '.png'
            file_ext = 'png'
            print(f"警告: 推定ベクターファイルサイズ ({estimated_size_mb:.1f}MB) が制限 ({max_vector_size_mb}MB) を超えるため、PNGに自動切り替えします。")
    
    if file_ext in ['pdf', 'svg']:
        # ベクター形式で保存
        plt.savefig(output_file, format=file_ext, bbox_inches='tight')
        print(f"ベクター画像を保存しました: {output_file}")
    else:
        # ラスター形式の場合はDPIを使用
        plt.savefig(output_file, dpi=dpi, bbox_inches='tight')
        if original_ext in ['pdf', 'svg']:
            print(f"PNG画像を保存しました: {output_file} (DPI: {dpi}) - ベクター形式から自動切り替え")
        else:
            print(f"画像を保存しました: {output_file} (DPI: {dpi})")
    plt.close()

def visualize_polygon_advanced(vertices, faces, title="3D Polygon Visualization", 
                             initial_alpha=0.8, initial_edge_width=0.1, 
                             show_vertices=False, lightweight_mode=False,
                             manual_point_size=None):
    """高度な3Dポリゴン可視化関数"""
    fig = plt.figure(figsize=(14, 10))
    
    # メインの3Dプロット
    ax = fig.add_subplot(111, projection='3d')
    plt.subplots_adjust(bottom=0.25)
    
    # 法線ベクトルを計算（シェーディング用）
    normals = calculate_face_normals(vertices, faces)
    
    # 三角形の重心を計算
    centroids = calculate_face_centroids(vertices, faces)
    
    # 光源の方向（簡易的なシェーディング）
    light_dir = np.array([1, 1, 1])
    light_dir = light_dir / np.linalg.norm(light_dir)
    
    # ポリゴンのコレクションを作成
    poly3d = []
    face_colors = []
    
    for i, face in enumerate(faces):
        # 各面の頂点座標を取得
        triangle = vertices[face]
        poly3d.append(triangle)
        
        # 簡易的なシェーディング（法線と光源の内積）
        shade = max(0.3, min(1.0, np.dot(normals[i], light_dir) * 0.7 + 0.5))
        face_colors.append((0, shade, shade))  # シアン系の色でシェーディング
    
    # 初期設定
    poly_collection = Poly3DCollection(poly3d, alpha=initial_alpha, 
                                     facecolors=face_colors,
                                     edgecolor='black', linewidth=initial_edge_width)
    ax.add_collection3d(poly_collection)
    
    # 軽量モード用の重心プロット（初期は非表示）
    centroid_plot = [None]
    lightweight_mode_state = [lightweight_mode]
    if manual_point_size is not None:
        point_size = manual_point_size
    else:
        point_size = calculate_adaptive_point_size(centroids)
    
    # 初期状態で軽量モードの場合
    if lightweight_mode:
        poly_collection.set_visible(False)
        centroid_plot[0] = ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2], 
                                     c='blue', s=point_size, alpha=0.6)
        ax.set_title(title + f" (Lightweight Mode, point size={point_size:.1f})")
    
    # 軸の範囲を設定（等縮尺）
    x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()
    y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
    z_min, z_max = vertices[:, 2].min(), vertices[:, 2].max()
    
    # 最大範囲を計算
    x_range = x_max - x_min
    y_range = y_max - y_min
    z_range = z_max - z_min
    max_range = max(x_range, y_range, z_range)
    
    # 各軸の中心を計算
    x_center = (x_max + x_min) / 2
    y_center = (y_max + y_min) / 2
    z_center = (z_max + z_min) / 2
    
    # 等縮尺で軸範囲を設定（1.1倍のマージンを追加）
    half_range = max_range * 1.1 / 2
    ax.set_xlim(x_center - half_range, x_center + half_range)
    ax.set_ylim(y_center - half_range, y_center + half_range)
    ax.set_zlim(z_center - half_range, z_center + half_range)
    
    # ラベルとタイトル
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(title)
    
    # グリッドを表示
    ax.grid(True)
    
    # 視点を設定
    ax.view_init(elev=20, azim=30)
    
    # スライダーの追加（透明度調整）
    ax_alpha = plt.axes([0.1, 0.15, 0.8, 0.03])
    slider_alpha = Slider(ax_alpha, 'Alpha', 0.1, 1.0, valinit=initial_alpha)
    
    # スライダーの追加（エッジ幅調整）
    ax_edge = plt.axes([0.1, 0.1, 0.8, 0.03])
    slider_edge = Slider(ax_edge, 'Edge Width', 0.0, 1.0, valinit=initial_edge_width)
    
    # スライダーの更新関数
    def update(val):
        poly_collection.set_alpha(slider_alpha.val)
        poly_collection.set_linewidth(slider_edge.val)
        fig.canvas.draw_idle()
    
    slider_alpha.on_changed(update)
    slider_edge.on_changed(update)
    
    # リセットボタン
    resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
    button = Button(resetax, 'Reset')
    
    def reset(event):
        slider_alpha.reset()
        slider_edge.reset()
    
    button.on_clicked(reset)
    
    # 頂点表示ボタン
    vertax = plt.axes([0.65, 0.025, 0.1, 0.04])
    vert_button = Button(vertax, 'Vertices')
    # 軽量モードでは頂点表示を無効にする
    vertices_shown = [show_vertices and not lightweight_mode_state[0]]
    scatter_plot = [None]
    
    # 初期状態で頂点表示の場合（軽量モードでは表示しない）
    if show_vertices and not lightweight_mode_state[0]:
        scatter_plot[0] = ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
                                   c='red', s=1, alpha=0.5)
    
    def toggle_vertices(event):
        if vertices_shown[0]:
            if scatter_plot[0]:
                scatter_plot[0].remove()
                scatter_plot[0] = None
            vertices_shown[0] = False
        else:
            scatter_plot[0] = ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
                                       c='red', s=1, alpha=0.5)
            vertices_shown[0] = True
        fig.canvas.draw_idle()
    
    vert_button.on_clicked(toggle_vertices)
    
    # 軽量モードボタン
    lightax = plt.axes([0.5, 0.025, 0.1, 0.04])
    light_button = Button(lightax, 'Lightweight')
    
    def toggle_lightweight(event):
        if lightweight_mode_state[0]:
            # 通常モードに戻す
            poly_collection.set_visible(True)
            if centroid_plot[0]:
                centroid_plot[0].remove()
                centroid_plot[0] = None
            lightweight_mode_state[0] = False
            ax.set_title(title)
        else:
            # 軽量モードに切り替え
            poly_collection.set_visible(False)
            centroid_plot[0] = ax.scatter(centroids[:, 0], centroids[:, 1], centroids[:, 2], 
                                         c='blue', s=point_size, alpha=0.6)
            lightweight_mode_state[0] = True
            ax.set_title(title + f" (Lightweight Mode, point size={point_size:.1f})")
        fig.canvas.draw_idle()
    
    light_button.on_clicked(toggle_lightweight)
    
    plt.show()

def main():
    # コマンドライン引数のパーサーを設定
    parser = argparse.ArgumentParser(description='3Dポリゴンデータの可視化ツール')
    parser.add_argument('filename', nargs='?', default='input_10ts.txt',
                       help='入力ファイル名（デフォルト: input_10ts.txt）')
    parser.add_argument('--alpha', '-a', type=float, default=0.8,
                       help='ポリゴンの透明度（0.1-1.0、デフォルト: 0.8）')
    parser.add_argument('--edge-width', '-e', type=float, default=0.1,
                       help='エッジの幅（0.0-1.0、デフォルト: 0.1）')
    parser.add_argument('--show-vertices', '-v', action='store_true',
                       help='起動時に頂点を表示')
    parser.add_argument('--lightweight', '-l', action='store_true',
                       help='軽量モード（三角形の重心のみ表示）で起動')
    parser.add_argument('--output', '-o', type=str,
                       help='画像ファイルとして保存（GUIを表示しない）。拡張子でフォーマット決定（.pdf, .svg, .png等）。拡張子なしの場合はPDF')
    parser.add_argument('--dpi', '-d', type=int, default=150,
                       help='出力画像のDPI（デフォルト: 150）')
    parser.add_argument('--elev', type=float, default=20,
                       help='視点の仰角（デフォルト: 20）')
    parser.add_argument('--azim', type=float, default=30,
                       help='視点の方位角（デフォルト: 30）')
    parser.add_argument('--point-size', '-p', type=float, default=None,
                       help='軽量モードでの点のサイズ（指定しない場合は自動調整）')
    parser.add_argument('--max-vector-size', type=float, default=5,
                       help='ベクター形式の最大ファイルサイズ（MB、デフォルト: 5）。これを超える場合は自動的にPNGに切り替え')
    
    args = parser.parse_args()
    
    # 画像出力モードの場合、バックエンドを設定
    if args.output:
        matplotlib.use('Agg')  # GUIなしのバックエンド
    
    # 引数の検証
    if not 0.1 <= args.alpha <= 1.0:
        print(f"警告: alphaは0.1-1.0の範囲で指定してください。{args.alpha}を0.8に変更します。")
        args.alpha = 0.8
    
    if not 0.0 <= args.edge_width <= 1.0:
        print(f"警告: edge-widthは0.0-1.0の範囲で指定してください。{args.edge_width}を0.1に変更します。")
        args.edge_width = 0.1
    
    try:
        # データを読み込む
        vertices, faces = read_polygon_data(args.filename)
        
        print(f"頂点データの形状: {vertices.shape}")
        print(f"面データの数: {len(faces)}")
        
        # 統計情報を表示
        print(f"\n座標の範囲:")
        print(f"X: [{vertices[:, 0].min():.3f}, {vertices[:, 0].max():.3f}]")
        print(f"Y: [{vertices[:, 1].min():.3f}, {vertices[:, 1].max():.3f}]")
        print(f"Z: [{vertices[:, 2].min():.3f}, {vertices[:, 2].max():.3f}]")
        
        # 面積の計算
        total_area = 0
        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            area = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0))
            total_area += area
        print(f"\n総表面積: {total_area:.3f}")
        
        # 重心の計算
        centroid = np.mean(vertices, axis=0)
        print(f"重心: [{centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f}]")
        
        # 可視化
        if args.output:
            # 出力ファイル名の処理（拡張子がない場合は.pdfを追加）
            output_file = args.output
            if '.' not in output_file.split('/')[-1]:  # ファイル名部分に拡張子がない
                output_file += '.pdf'
            
            # 非インタラクティブモード（画像ファイル出力）
            visualize_polygon_noninteractive(vertices, faces, output_file,
                                           dpi=args.dpi,
                                           elev=args.elev,
                                           azim=args.azim,
                                           title=f"3D Polygon: {args.filename}",
                                           initial_alpha=args.alpha,
                                           initial_edge_width=args.edge_width,
                                           show_vertices=args.show_vertices,
                                           lightweight_mode=args.lightweight,
                                           manual_point_size=args.point_size,
                                           max_vector_size_mb=args.max_vector_size)
        else:
            # インタラクティブモード（GUI表示）
            visualize_polygon_advanced(vertices, faces, f"3D Polygon: {args.filename}",
                                     initial_alpha=args.alpha,
                                     initial_edge_width=args.edge_width,
                                     show_vertices=args.show_vertices,
                                     lightweight_mode=args.lightweight,
                                     manual_point_size=args.point_size)
        
    except FileNotFoundError:
        print(f"エラー: ファイル '{args.filename}' が見つかりません。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()