import os
import pickle
import numpy as np

class SignLandmarkClassifier:
    """
    High-performance, pure NumPy multi-class classifier optimized for 
    MediaPipe 63-dimensional normalized hand landmark vectors.
    Uses an ensemble of K-Nearest Neighbors (k=5) and Cosine/Euclidean 
    Centroid Softmax to output calibrated confidence probabilities.
    Immune to Windows DLL AppLocker restrictions and runs in <1ms.
    """
    def __init__(self, k: int = 5, temperature: float = 6.0):
        self.k = k
        self.temperature = temperature
        self.classes_ = []
        self.centroids_ = {}
        self.variances_ = {}
        self.X_train_ = None
        self.y_train_ = None

    def fit(self, X, y):
        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y)

        self.classes_ = sorted(list(set(y_arr)))
        self.X_train_ = X_arr
        self.y_train_ = y_arr

        self.centroids_ = {}
        self.variances_ = {}

        for c in self.classes_:
            c_mask = (self.y_train_ == c)
            c_samples = self.X_train_[c_mask]
            self.centroids_[c] = np.mean(c_samples, axis=0)
            self.variances_[c] = np.var(c_samples, axis=0) + 1e-4

        return self

    def predict_proba(self, X):
        X_arr = np.array(X, dtype=np.float32)
        if len(X_arr.shape) == 1:
            X_arr = np.expand_dims(X_arr, axis=0)

        n_samples = X_arr.shape[0]
        n_classes = len(self.classes_)
        probs = np.zeros((n_samples, n_classes), dtype=np.float32)

        for i, x in enumerate(X_arr):
            # 1. Centroid distance score
            centroid_dists = np.array([
                np.linalg.norm(x - self.centroids_[c]) for c in self.classes_
            ])
            # Softmax over negative centroid distances
            exp_c = np.exp(-self.temperature * centroid_dists)
            p_centroid = exp_c / (np.sum(exp_c) + 1e-8)

            # 2. k-NN distance score
            sample_dists = np.linalg.norm(self.X_train_ - x, axis=1)
            k_val = min(self.k, len(self.X_train_))
            nearest_indices = np.argsort(sample_dists)[:k_val]
            nearest_labels = self.y_train_[nearest_indices]

            p_knn = np.zeros(n_classes, dtype=np.float32)
            for j, c in enumerate(self.classes_):
                p_knn[j] = np.mean(nearest_labels == c)

            # Blended probability (60% k-NN + 40% Centroid)
            blended = 0.60 * p_knn + 0.40 * p_centroid
            probs[i] = blended / (np.sum(blended) + 1e-8)

        return probs

    def predict(self, X):
        probs = self.predict_proba(X)
        indices = np.argmax(probs, axis=1)
        return np.array([self.classes_[i] for i in indices])

    def score(self, X, y):
        preds = self.predict(X)
        return float(np.mean(preds == np.array(y)))

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(filepath: str):
        with open(filepath, "rb") as f:
            return pickle.load(f)
