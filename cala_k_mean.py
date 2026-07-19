#!/usr/bin/env python3
print(f"\n" + "=" * 100)
print(f"== RUN {__file__} ==")  
print(f"=" * 100 + "\n")
# =============================================================================================
# ==== INFORMATION ========
# ========================
# 檔名: ensemble_kmeans_clustering.py
# 功能: 對降水系集數據進行K-means分群分析，可自訂變數和輸出路徑
# 作者: CYC
# 建立日期: 2025-06-09
#
# Description:
#   此程式讀取CSV格式的降水系集數據，執行K-means分群分析。
#   使用者可自訂要用於分群的變數組合，支援肘部法則和輪廓分析確定最佳分群數。
#   生成多種視覺化圖表分析分群結果，包括PCA降維圖、特徵熱力圖等。
# ============================================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import warnings
import argparse
import os
import sys
warnings.filterwarnings('ignore')

#---------------------------------------
""" 全局變數 """
DPI = 200  # 解析度

# 使用明確區分的飽和色彩
D_COLOR = ['#FF4444', '#4444FF', '#44FF44', '#FF8800', 
          '#8800FF', '#00FFFF', '#FF00FF', '#FFFF00',
          '#800000', '#008000', '#000080', '#808000']
        
#---------------------------------------

def parse_arguments():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description='對系集數據進行K-means分群分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基本使用 - 使用預設變數進行分群
  python3 ensemble_kmeans_clustering.py -i rainfall_data.csv

  # 指定要用於分群的變數
  python3 ensemble_kmeans_clustering.py -i rainfall_data.csv -V P1_peak_time_idx,P1_peak_value,P2_peak_time_idx,P2_peak_value

  # 指定輸出目錄
  python3 ensemble_kmeans_clustering.py -i rainfall_data.csv -n ./output_clustering

  # 完整參數設定
  python3 ensemble_kmeans_clustering.py -i rainfall_data.csv -V P1_peak_time_idx,P1_peak_value,P2_peak_time_idx,P2_peak_value,gap_time_idx,gap_value -n ./clustering_results -k 5

作者: CYC
建立日期: 2025-06-09 [v1.0]
        """)

    # 必要參數
    parser.add_argument('-i', '--input', 
                       default='rainfall_peaks_results.csv',
                       help='輸入CSV檔案路徑 (預設: rainfall_peaks_results.csv)')
    
    # 選用參數
    parser.add_argument('-V', '--variables',
                       default='P1_peak_time_idx,P1_peak_value,P2_peak_time_idx,P2_peak_value,gap_time_idx,gap_value',
                       help='用於分群的變數名稱，以逗號分隔 [預設: 6個降水參數(P1_peak_time_idx,P1_peak_value,P2_peak_time_idx,P2_peak_value,gap_time_idx,gap_value)]')
    
    parser.add_argument('-n', '--output_dir',
                       default='./output_cala_k',
                       help='輸出目錄路徑 (預設: ./output_cala_k)')
    
    parser.add_argument('-n_c', '--n_clusters',
                       type=int, default=None,
                       help='指定分群數量 (預設: 自動確定)')
    
    parser.add_argument('-max_k', '--max_clusters',
                       type=int, default=12,
                       help='分析的最大分群數量 (預設: 12)')
    
    return parser.parse_args()

def ensure_output_directory(output_dir):
    """確保輸出目錄存在"""
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
        except Exception as e:
            print(f"Error creating directory: {str(e)}")
            return "./"
    return output_dir

class EnsembleRainfallClustering:
    def __init__(self, csv_file_path, feature_names, output_dir):
        """
        初始化降水系集分群分析類別
        
        Parameters:
        csv_file_path: str, CSV文件路徑
        feature_names: list, 用於分群的特徵名稱列表
        output_dir: str, 輸出目錄路徑
        """
        self.csv_file_path = csv_file_path
        self.output_dir = output_dir
        self.data = None
        self.X = None
        self.X_scaled = None
        self.scaler = None
        self.feature_names = feature_names
        self.kmeans_model = None
        self.cluster_labels = None
        self.optimal_k = None
        
        # 設定圖表參數
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        sns.set_palette("husl")
        
    def load_and_prepare_data(self):
        """載入並準備數據"""
        print(f"\nLoading rainfall ensemble data...")
        
        # 檢查輸入檔案是否存在
        if not os.path.exists(self.csv_file_path):
            print(f"Error: Input file not found: {self.csv_file_path}")
            sys.exit(1)
        
        # 讀取CSV數據
        try:
            self.data = pd.read_csv(self.csv_file_path)
            print(f"    Data shape: {self.data.shape}")
            print(f"    Members: {len(self.data)}")
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            sys.exit(1)
        
        # 顯示數據基本資訊
        print(f"    Available columns: {self.data.columns.tolist()}")
        
        # 檢查所需欄位是否存在
        missing_cols = [col for col in self.feature_names if col not in self.data.columns]
        if missing_cols:
            print(f"Error: Missing columns in data: {missing_cols}")
            print(f"Available columns: {self.data.columns.tolist()}")
            sys.exit(1)
        
        self.X = self.data[self.feature_names].values
        
        print(f"    Selected {len(self.feature_names)} variables for clustering:")
        for i, feature in enumerate(self.feature_names):
            print(f"        {i+1}. {feature}")
        
        # 檢查缺失值
        if np.isnan(self.X).any():
            print("    Warning: Found NaN values in data. Removing rows with NaN...")
            valid_rows = ~np.isnan(self.X).any(axis=1)
            self.X = self.X[valid_rows]
            self.data = self.data[valid_rows].reset_index(drop=True)
            print(f"    Data shape after removing NaN: {self.X.shape}")
        
        return self.X
    
    def standardize_data(self):
        """數據標準化"""
        print(f"\nStandardizing data...")
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        
        # 顯示標準化前後的統計資訊
        print("    Data statistics before standardization:")
        df_stats = pd.DataFrame(self.X, columns=self.feature_names)
        print(df_stats.describe().round(3))
        
        return self.X_scaled
    
    def elbow_method_analysis(self, max_k=12):
        """肘部法則分析確定最佳k值"""
        print(f"\nPerforming elbow method analysis (k=1 to {max_k})...")
        
        k_range = range(1, max_k + 1)
        wcss = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(self.X_scaled)
            wcss.append(kmeans.inertia_)
        
        # 繪製肘部圖
        plt.figure(figsize=(8, 8))
        plt.plot(k_range, wcss, marker='o', linewidth=2, markersize=8, color='blue')
        plt.title('Elbow Method for Optimal Number of Clusters\n(Ensemble Rainfall Patterns)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Number of Clusters (k)', fontsize=12)
        plt.ylabel('Within-Cluster Sum of Squares (WCSS)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(k_range)
        
        # 標記可能的肘部點
        if len(wcss) > 3:
            # 計算二階差分來找肘部
            diff1 = np.diff(wcss)
            diff2 = np.diff(diff1)
            elbow_idx = np.argmax(diff2) + 2
            if elbow_idx < len(k_range):
                plt.axvline(x=k_range[elbow_idx], color='red', linestyle='--', 
                           alpha=0.7, label=f'Suggested k={k_range[elbow_idx]}')
                plt.legend()
        
        plt.tight_layout()
        
        # 保存圖片
        output_path = os.path.join(self.output_dir, 'elbow_method.png')
        plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
        print(f"    Elbow method plot saved: {output_path}")
        plt.close()
        
        return wcss
    
    def silhouette_analysis(self, max_k=12):
        """輪廓分析評估分群品質"""
        print(f"\nPerforming silhouette analysis (k=2 to {max_k})...")
        
        k_range = range(2, max_k + 1)
        silhouette_scores = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(self.X_scaled)
            silhouette_avg = silhouette_score(self.X_scaled, cluster_labels)
            silhouette_scores.append(silhouette_avg)
            print(f"    k={k}: Silhouette Score = {silhouette_avg:.4f}")
        
        # 找出最佳k值
        best_k_idx = np.argmax(silhouette_scores)
        best_k = k_range[best_k_idx]
        best_score = silhouette_scores[best_k_idx]
        
        print(f"    Best k based on silhouette score: {best_k} (score: {best_score:.4f})")
        
        # 繪製輪廓分數圖
        plt.figure(figsize=(8, 8))
        plt.plot(k_range, silhouette_scores, marker='o', linewidth=2, markersize=8, color='green')
        plt.axvline(x=best_k, color='red', linestyle='--', alpha=0.7, 
                   label=f'Best k={best_k} (score={best_score:.4f})')
        plt.title('Silhouette Analysis for Optimal Number of Clusters\n(Ensemble Rainfall Patterns)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Number of Clusters (k)', fontsize=12)
        plt.ylabel('Average Silhouette Score', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(k_range)
        plt.legend()
        plt.tight_layout()
        
        # 保存圖片
        output_path = os.path.join(self.output_dir, 'silhouette_analysis.png')
        plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
        print(f"    Silhouette analysis plot saved: {output_path}")
        plt.close()
        
        self.optimal_k = best_k
        return silhouette_scores, best_k
    
    def perform_clustering(self, n_clusters=None):
        """執行k-means分群"""
        if n_clusters is None:
            n_clusters = self.optimal_k if self.optimal_k else 4
        
        print(f"\nPerforming K-means clustering with k={n_clusters}...")
        
        self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans_model.fit_predict(self.X_scaled)
        
        # 將分群結果加入原始數據
        self.data['cluster'] = self.cluster_labels
        
        # 評估分群品質
        silhouette_avg = silhouette_score(self.X_scaled, self.cluster_labels)
        print(f"    Average Silhouette Score: {silhouette_avg:.4f}")
        
        # 顯示各群組大小
        unique, counts = np.unique(self.cluster_labels, return_counts=True)
        print(f"    Cluster sizes:")
        for cluster, count in zip(unique, counts):
            percentage = (count / len(self.cluster_labels)) * 100
            print(f"        Cluster {cluster + 1}: {count} members ({percentage:.1f}%)")
        
        return self.cluster_labels
    
    def analyze_cluster_characteristics(self):
        """分析各群組的降水特徵"""
        print(f"\n=== Cluster Characteristics Analysis ===")
        
        # 計算各群組的特徵統計
        cluster_stats = []
        
        for cluster_id in range(len(np.unique(self.cluster_labels))):
            cluster_data = self.data[self.data['cluster'] == cluster_id]
            stats = {}
            stats['cluster'] = cluster_id + 1
            stats['size'] = len(cluster_data)
            
            for feature in self.feature_names:
                stats[f'{feature}_mean'] = cluster_data[feature].mean()
                stats[f'{feature}_std'] = cluster_data[feature].std()
            
            cluster_stats.append(stats)
        
        cluster_stats_df = pd.DataFrame(cluster_stats)
        
        # 顯示主要降水參數的平均值比較
        print("    Variable characteristics by cluster:")
        
        for feature in self.feature_names:
            if f'{feature}_mean' in cluster_stats_df.columns:
                print(f"        {feature}:")
                for _, row in cluster_stats_df.iterrows():
                    print(f"            Cluster {int(row['cluster'])}: {row[f'{feature}_mean']:.2f} ± {row[f'{feature}_std']:.2f}")
        
        return cluster_stats_df
    
    def visualize_clusters_2d(self):
        """使用PCA降維視覺化分群結果"""
        print(f"\nCreating 2D visualization using PCA...")
        
        # PCA降維到2D
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(self.X_scaled)
        
        plt.figure(figsize=(14, 10))

        # 確保有足夠的顏色
        n_clusters = len(np.unique(self.cluster_labels))
        if n_clusters > len(D_COLOR):
            # 如果群組數量超過預定義顏色，使用tab10色彩映射
            colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))
        else:
            colors = D_COLOR[:n_clusters]
        
        for i, cluster_id in enumerate(np.unique(self.cluster_labels)):
            cluster_mask = self.cluster_labels == cluster_id
            plt.scatter(X_pca[cluster_mask, 0], X_pca[cluster_mask, 1], 
                       c=colors[i], label=f'Cluster {cluster_id + 1}', 
                       alpha=0.8, s=80, edgecolors='black', linewidth=0.8)
        
        # 繪製群心在PCA空間中的位置，使用對應顏色的X標記
        centroids_pca = pca.transform(self.kmeans_model.cluster_centers_)
        for i, cluster_id in enumerate(np.unique(self.cluster_labels)):
            plt.scatter(centroids_pca[cluster_id, 0], centroids_pca[cluster_id, 1], 
                       c=colors[i], marker='X', s=300, linewidths=1, 
                       edgecolors='black', label=f'Centroid {cluster_id + 1}') 
        
        plt.title('K-means Clustering Visualization (PCA)\nBased on Selected Variables', 
                 fontsize=18, fontweight='bold')
        plt.xlabel(f'First Principal Component (explained variance: {pca.explained_variance_ratio_[0]:.2%})', 
                  fontsize=16)
        plt.ylabel(f'Second Principal Component (explained variance: {pca.explained_variance_ratio_[1]:.2%})', 
                  fontsize=16)
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 保存圖片
        output_path = os.path.join(self.output_dir, 'pca_clustering.png')
        plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
        print(f"    PCA clustering plot saved: {output_path}")
        plt.close()
        
        print(f"    Total explained variance: {pca.explained_variance_ratio_.sum():.2%}")
        
        return X_pca, pca
    
    def create_feature_heatmap(self):
        """創建特徵熱力圖比較各群組"""
        print(f"\nCreating feature comparison heatmap...")
        
        # 計算各群組的標準化特徵平均值
        cluster_means = []
        for cluster_id in range(len(np.unique(self.cluster_labels))):
            cluster_mask = self.cluster_labels == cluster_id
            cluster_mean = np.mean(self.X_scaled[cluster_mask], axis=0)
            cluster_means.append(cluster_mean)
        
        cluster_means = np.array(cluster_means)
        
        # 創建熱力圖
        plt.figure(figsize=(max(16, len(self.feature_names) * 2), 8))
        
        # 縮短特徵名稱以便顯示
        short_feature_names = []
        for name in self.feature_names:
            if len(name) > 15:
                short_name = name.replace('_', '\n')
                short_feature_names.append(short_name)
            else:
                short_feature_names.append(name)
        
        sns.heatmap(cluster_means, 
                   xticklabels=short_feature_names,
                   yticklabels=[f'Cluster {i+1}' for i in range(len(cluster_means))],
                   annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                   cbar_kws={'label': 'Standardized Value'})
        
        plt.title(f'Variable Characteristics by Cluster\n({len(self.feature_names)} Selected Variables)', 
                 fontsize=16, fontweight='bold')
        plt.xlabel('Variables', fontsize=12)
        plt.ylabel('Cluster Groups', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # 保存圖片
        output_path = os.path.join(self.output_dir, 'feature_heatmap.png')
        plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
        print(f"    Feature heatmap saved: {output_path}")
        plt.close()
    def create_pairwise_scatter_plots(self):
        """創建變數間的散點圖矩陣"""
        print(f"\nCreating pairwise scatter plots...")
    
        # 限制變數數量避免圖太大
        max_vars = 10
        if len(self.feature_names) > max_vars:
            print(f"    Too many variables ({len(self.feature_names)}), showing first {max_vars} variables")
            selected_features = self.feature_names[:max_vars]
        else:
            selected_features = self.feature_names
    
        n_features = len(selected_features)
        fig, axes = plt.subplots(n_features, n_features, figsize=(3*n_features+1.5, 3*n_features))
    
        # 如果只有一個變數，axes不是二維數組
        if n_features == 1:
            axes = [[axes]]
        elif n_features == 2:
            axes = [axes] if len(axes.shape) == 1 else axes
    
        # 使用與PCA圖相同的顏色方案
        n_clusters = len(np.unique(self.cluster_labels))
        if n_clusters > len(D_COLOR):
            # 如果群組數量超過預定義顏色，使用tab10色彩映射
            colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))
        else:
            colors = D_COLOR[:n_clusters]
    
        for i, feature_x in enumerate(selected_features):
            for j, feature_y in enumerate(selected_features):
                ax = axes[i][j] if n_features > 1 else axes[0][0]
    
                if i == j:
                    # 對角線顯示直方圖
                    for k, cluster_id in enumerate(np.unique(self.cluster_labels)):
                        cluster_data = self.data[self.data['cluster'] == cluster_id]
                        ax.hist(cluster_data[feature_x], alpha=0.7,
                               label=f'Cluster {cluster_id + 1}', bins=15,
                               color=colors[k])  # 使用對應的顏色
                    ax.set_xlabel(feature_x)
                    ax.set_ylabel('Frequency')
                else:
                    # 非對角線顯示散點圖
                    for k, cluster_id in enumerate(np.unique(self.cluster_labels)):
                        cluster_data = self.data[self.data['cluster'] == cluster_id]
                      #  ax.scatter(cluster_data[feature_x], cluster_data[feature_y],
                        ax.scatter(cluster_data[feature_y], cluster_data[feature_x],
                                 label=f'Cluster {cluster_id + 1}', alpha=0.8, s=20,
                                 c=colors[k])  # 使用對應的顏色
                    ax.set_xlabel(feature_y)
                    ax.set_ylabel(feature_x)
    
                ax.grid(True, alpha=0.3)

        # 將圖例放在第一列最後一個子圖的外側
        legend_ax = axes[0][-1] if n_features > 1 else axes[0][0]
        legend_ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
 
        # title
        plt.suptitle('Pairwise Variable Relationships by Clusters', fontsize=20, fontweight='bold')
        plt.tight_layout()
    
        # 保存圖片
        output_path = os.path.join(self.output_dir, 'pairwise_scatter.png')
        plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
        print(f"    Pairwise scatter plots saved: {output_path}")
        plt.close()    
        
    def export_results(self, output_file='clustering_results.csv'):
        """匯出分群結果"""
        print(f"\nExporting clustering results...")
        
        # 準備輸出數據
        output_data = self.data.copy()
        
        # 添加額外資訊
        output_data['cluster_id'] = self.cluster_labels + 1
        
        # 計算每個成員到其群心的距離
        distances = []
        for i, member_data in enumerate(self.X_scaled):
            cluster_id = self.cluster_labels[i]
            centroid = self.kmeans_model.cluster_centers_[cluster_id]
            distance = np.linalg.norm(member_data - centroid)
            distances.append(distance)
        
        output_data['distance_to_centroid'] = distances
        
        # 儲存結果
        output_path = os.path.join(self.output_dir, output_file)
        output_data.to_csv(output_path, index=False)
        print(f"    Results saved to {output_path}")
        
        return output_data

def main():
    """主要執行函數"""
    # 解析命令列參數
    args = parse_arguments()
    
    # 解析變數名稱
    feature_names = [var.strip() for var in args.variables.split(',')]
    
    # 確保輸出目錄存在
    output_dir = ensure_output_directory(args.output_dir)

    print(f"\n{50*'-'}\n--- Ensemble K-means Clustering Analysis ---\n{50*'-'}")
    print(f"Input file: {args.input}")
    print(f"Variables for clustering: {feature_names}")
    print(f"Output directory: {output_dir}")
    if args.n_clusters:
        print(f"Specified number of clusters: {args.n_clusters}")
    
    # 創建分析物件
    rainfall_clustering = EnsembleRainfallClustering(args.input, feature_names, output_dir)
    
    try:
        # 1. 載入和準備數據
        rainfall_clustering.load_and_prepare_data()
        
        # 2. 數據標準化
        rainfall_clustering.standardize_data()
        
        # 3. 確定最佳分群數量 (如果未指定)
        if args.n_clusters is None:
            rainfall_clustering.elbow_method_analysis(max_k=args.max_clusters)
            rainfall_clustering.silhouette_analysis(max_k=args.max_clusters)
        
        # 4. 執行分群
        rainfall_clustering.perform_clustering(n_clusters=args.n_clusters)
        
        # 5. 分析群組特徵
        cluster_stats = rainfall_clustering.analyze_cluster_characteristics()
        
        # 6. 視覺化結果
        rainfall_clustering.visualize_clusters_2d()
        rainfall_clustering.create_feature_heatmap()
        rainfall_clustering.create_pairwise_scatter_plots()
        
        # 7. 匯出結果
        results = rainfall_clustering.export_results('clustering_results.csv')
        
        print("\n=== Clustering Analysis Complete ===")
        print(f"All results saved in: {output_dir}")
        
        return rainfall_clustering
        
    except FileNotFoundError:
        print(f"!!! Error: Cannot find file {args.input} !!!")
        print("!!! Please check the file path and make sure the file exists. !!!")
        return None
    except Exception as e:
        print(f"!!! Error during analysis: {str(e)} !!!")
        return None

# =============================================================================================
if __name__ == "__main__":
    clustering_analysis = main()

print(f"\n" + "=" * 100)
print(f"== RUN END {__file__} ==")  
print(f"=" * 100 + "\n")
# =============================================================================================
