"""
Modelo de Machine Learning para predicción de precios de tarjetas deportivas

Este módulo implementa un modelo de Gradient Boosting para predecir
el precio futuro de tarjetas deportivas basado en múltiples features.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Resultado de una predicción de precio"""

    predicted_price: float
    confidence: float  # 0-1
    trend: str  # "up", "down", "stable"
    trend_percentage: float
    price_range_low: float
    price_range_high: float
    factors: list[dict[str, Any]]
    model_version: str
    prediction_date: datetime


class PricePredictor:
    """
    Modelo de predicción de precios para tarjetas deportivas

    Features utilizados:
    - Características de la tarjeta: año, grade, marca, rookie, autógrafo, patch, paralelo
    - Datos del mercado: precio promedio, desviación estándar, volumen, tendencia
    - Datos del jugador: score de rendimiento, sentimiento, años en la liga
    """

    MODEL_VERSION = "1.0.0"

    def __init__(self, model_type: str = "gradient_boosting"):
        """
        Inicializa el modelo de predicción

        Args:
            model_type: Tipo de modelo ('gradient_boosting' o 'random_forest')
        """
        self.model_type = model_type
        self.model: GradientBoostingRegressor | RandomForestRegressor | None = None
        self.scaler: StandardScaler | None = None
        self.feature_encoder: LabelEncoder | None = None
        self.feature_names: list[str] = []
        self.is_trained = False

        # Definir features del modelo
        self._define_features()

    def _define_features(self):
        """Define los features utilizados por el modelo"""
        self.feature_names = [
            # Features de la tarjeta
            "year",
            "grade",
            "is_rookie_card",
            "is_autograph",
            "is_patch",
            "is_parallel",
            "card_number_normalized",
            # Features del mercado
            "market_price_mean",
            "market_price_std",
            "market_volume_30d",
            "market_trend_slope",
            # Features del jugador
            "player_performance_score",
            "player_sentiment_score",
            "player_years_in_league",
            "player_all_star_count",
            "player_mvp_count",
            # Features de escasez
            "edition_size",
            "print_run",
            # Features de categoría
            "sport_encoded",
            "brand_encoded",
        ]

    def _extract_features(
        self, card_data: dict[str, Any], market_data: dict[str, Any], player_data: dict[str, Any]
    ) -> np.ndarray:
        """
        Extrae features de los datos de entrada

        Args:
            card_data: Datos de la tarjeta
            market_data: Datos del mercado
            player_data: Datos del jugador

        Returns:
            Array de features
        """
        features = []

        # Features de la tarjeta
        year = card_data.get("year", 2000)
        current_year = datetime.now().year
        features.append(year)
        features.append(card_data.get("grade", 5.0))

        # Detectar tipos especiales de tarjeta
        title = card_data.get("title", "").lower()
        features.append(1 if "rookie" in title else 0)
        features.append(1 if "auto" in title or "autograph" in title else 0)
        features.append(1 if "patch" in title or "game used" in title else 0)
        features.append(1 if "refractor" in title or "parallel" in title else 0)

        # Número de tarjeta normalizado (0-1)
        card_num = card_data.get("card_number", "0")
        try:
            num = int("".join(filter(str.isdigit, str(card_num))))
            features.append(min(num / 100, 1.0))  # Normalizar a 0-1
        except:
            features.append(0.0)

        # Features del mercado
        features.append(market_data.get("price_mean", 100.0))
        features.append(market_data.get("price_std", 0.0))
        features.append(market_data.get("volume_30d", 0))
        features.append(market_data.get("trend_slope", 0.0))

        # Features del jugador
        features.append(player_data.get("performance_score", 50.0))
        features.append(player_data.get("sentiment_score", 0.0))
        features.append(player_data.get("years_in_league", 1))
        features.append(player_data.get("all_star_count", 0))
        features.append(player_data.get("mvp_count", 0))

        # Features de escasez (usando año como proxy)
        years_since_issue = current_year - year
        if years_since_issue < 2:
            features.append(1.0)  # Muy reciente
        elif years_since_issue < 5:
            features.append(0.7)
        elif years_since_issue < 10:
            features.append(0.5)
        else:
            features.append(0.3)

        features.append(1.0)  # placeholder para print_run

        # Features categóricos (encoding simplificado)
        sport_map = {"NBA": 0, "NFL": 1, "MLB": 2, "NHL": 3, "Soccer": 4}
        features.append(sport_map.get(player_data.get("sport", "NBA"), 0))

        brand_map = {"Topps": 0, "Panini": 1, "Upper Deck": 2, "Fleer": 3, "Bowman": 4}
        features.append(brand_map.get(card_data.get("brand", "Topps"), 0))

        return np.array(features).reshape(1, -1)

    def train(
        self,
        data: pd.DataFrame,
        target_column: str = "sale_price",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict[str, float]:
        """
        Entrena el modelo con datos históricos

        Args:
            data: DataFrame con los datos de entrenamiento
            target_column: Nombre de la columna objetivo
            test_size: Proporción del test set
            random_state: Semilla aleatoria

        Returns:
            Métricas del modelo
        """
        # Verificar que existen las columnas necesarias
        required_features = [f for f in self.feature_names if f in data.columns]
        if len(required_features) < 5:
            logger.warning("Datos insuficientes para entrenar. Usando modelo simulado.")
            self.is_trained = False
            return {"error": "Datos insuficientes"}

        # Preparar datos
        X = data[required_features].fillna(0)
        y = data[target_column].fillna(0)

        # Split datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Escalar features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Crear modelo
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1,
            )
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
            )

        # Entrenar
        self.model.fit(X_train_scaled, y_train)

        # Evaluar
        y_pred = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Calcular confidence basado en R²
        confidence = max(0.0, min(1.0, r2))

        self.is_trained = True
        self.feature_names = required_features

        logger.info(f"[PricePredictor] Modelo entrenado. R²: {r2:.3f}, MAE: ${mae:.2f}")

        return {"r2_score": r2, "mae": mae, "rmse": rmse, "confidence": confidence}

    def predict(
        self, card_data: dict[str, Any], market_data: dict[str, Any], player_data: dict[str, Any]
    ) -> PredictionResult:
        """
        Predice el precio de una tarjeta

        Args:
            card_data: Datos de la tarjeta
            market_data: Datos del mercado
            player_data: Datos del jugador

        Returns:
            PredictionResult con la predicción
        """
        # Extraer features
        features = self._extract_features(card_data, market_data, player_data)

        if not self.is_trained or self.model is None:
            # Usar estimación basada en mercado
            base_price = market_data.get("price_mean", 100.0)
            predicted_price = base_price

            # Ajustar por grade
            grade = card_data.get("grade", 5.0)
            if grade >= 10:
                predicted_price *= 2.0
            elif grade >= 9:
                predicted_price *= 1.5
            elif grade >= 8:
                predicted_price *= 1.2

            confidence = 0.5  # Baja confianza sin modelo entrenado
        else:
            # Escalar y predecir
            features_scaled = self.scaler.transform(features)
            predicted_price = self.model.predict(features_scaled)[0]

            # Calcular confidence basado en el mercado
            price_std = market_data.get("price_std", 0)
            price_mean = market_data.get("price_mean", 100)
            if price_std > 0 and price_mean > 0:
                cv = price_std / price_mean  # Coeficiente de variación
                confidence = max(0.3, min(0.95, 1 - cv))
            else:
                confidence = 0.7

        # Calcular tendencia
        trend_slope = market_data.get("trend_slope", 0.0)
        if trend_slope > 0.05:
            trend = "up"
            trend_percentage = trend_slope * 100
        elif trend_slope < -0.05:
            trend = "down"
            trend_percentage = abs(trend_slope) * 100
        else:
            trend = "stable"
            trend_percentage = 0.0

        # Calcular rango de precio
        margin = 1 - (confidence * 0.3)  # Mayor confianza = menor margen
        price_range_low = predicted_price * (1 - margin)
        price_range_high = predicted_price * (1 + margin)

        # Generar factores que afectan el precio
        factors = self._generate_factors(card_data, market_data, player_data)

        return PredictionResult(
            predicted_price=max(0, predicted_price),
            confidence=confidence,
            trend=trend,
            trend_percentage=trend_percentage,
            price_range_low=price_range_low,
            price_range_high=price_range_high,
            factors=factors,
            model_version=self.MODEL_VERSION,
            prediction_date=datetime.now(),
        )

    def _generate_factors(
        self, card_data: dict[str, Any], market_data: dict[str, Any], player_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Genera lista de factores que afectan el precio"""
        factors = []

        # Factor grade
        grade = card_data.get("grade", 5.0)
        if grade >= 10:
            factors.append(
                {
                    "factor": "Grade Perfecto",
                    "impact": "positive",
                    "description": "PSA/BGS 10 maximiza el valor",
                }
            )
        elif grade >= 9:
            factors.append(
                {
                    "factor": "Grade Alto",
                    "impact": "positive",
                    "description": "Grade 9+ mantiene buen valor",
                }
            )

        # Factor rookie
        title = card_data.get("title", "").lower()
        if "rookie" in title:
            factors.append(
                {
                    "factor": "Tarjeta de Rookie",
                    "impact": "positive",
                    "description": "Las rookie cards son más valiosas",
                }
            )

        # Factor autógrafo
        if "auto" in title or "autograph" in title:
            factors.append(
                {
                    "factor": "Autógrafo",
                    "impact": "positive",
                    "description": "Las cartas firmadas tienen prima",
                }
            )

        # Factor tendencia del mercado
        trend_slope = market_data.get("trend_slope", 0)
        if trend_slope > 0:
            factors.append(
                {
                    "factor": "Mercado en Alza",
                    "impact": "positive",
                    "description": f"Tendencia positiva del {abs(trend_slope) * 100:.1f}%",
                }
            )
        elif trend_slope < 0:
            factors.append(
                {
                    "factor": "Mercado en Baja",
                    "impact": "negative",
                    "description": f"Tendencia negativa del {abs(trend_slope) * 100:.1f}%",
                }
            )

        # Factor rendimiento del jugador
        perf_score = player_data.get("performance_score", 50)
        if perf_score >= 80:
            factors.append(
                {
                    "factor": "Jugador Elite",
                    "impact": "positive",
                    "description": "Alto rendimiento del jugador",
                }
            )
        elif perf_score < 40:
            factors.append(
                {
                    "factor": "Jugador en Desarrollo",
                    "impact": "neutral",
                    "description": "Rendimiento por desarrollar",
                }
            )

        return factors

    def get_feature_importance(self) -> dict[str, float]:
        """
        Obtiene la importancia de cada feature

        Returns:
            Dict con feature -> importancia
        """
        if not self.is_trained or self.model is None:
            return {}

        importances = self.model.feature_importances_
        return dict(zip(self.feature_names, importances))


# Instancia global del predictor
_predictor_instance: PricePredictor | None = None


def get_price_predictor() -> PricePredictor:
    """Obtiene la instancia global del predictor"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PricePredictor()
    return _predictor_instance
