"""
Tests unitarios para PricePredictor
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.ml.price_predictor import PredictionResult, PricePredictor


class TestPricePredictor:
    """Tests para PricePredictor"""

    @pytest.fixture
    def predictor(self):
        """Crea una instancia del predictor"""
        return PricePredictor(model_type="gradient_boosting")

    @pytest.fixture
    def sample_card_data(self):
        """Datos de ejemplo de una tarjeta"""
        return {
            "title": "2003 Topps LeBron James Rookie Chrome Refractor Auto #1",
            "year": 2003,
            "grade": 9.5,
            "brand": "Topps",
            "card_number": "1",
        }

    @pytest.fixture
    def sample_market_data(self):
        """Datos de ejemplo del mercado"""
        return {
            "price_mean": 500.0,
            "price_std": 100.0,
            "volume_30d": 25,
            "trend_slope": 0.02,
        }

    @pytest.fixture
    def sample_player_data(self):
        """Datos de ejemplo del jugador"""
        return {
            "performance_score": 85.0,
            "sentiment_score": 0.7,
            "years_in_league": 20,
            "all_star_count": 20,
            "mvp_count": 4,
            "sport": "NBA",
        }

    def test_predictor_initialization(self, predictor):
        """Test de inicialización del predictor"""
        assert predictor.model_type == "gradient_boosting"
        assert predictor.is_trained is False
        assert predictor.MODEL_VERSION == "1.0.0"
        assert len(predictor.feature_names) > 0

    def test_define_features(self, predictor):
        """Test de definición de features"""
        assert "year" in predictor.feature_names
        assert "grade" in predictor.feature_names
        assert "is_rookie_card" in predictor.feature_names
        assert "market_price_mean" in predictor.feature_names

    def test_extract_features(
        self, predictor, sample_card_data, sample_market_data, sample_player_data
    ):
        """Test de extracción de features"""
        features = predictor._extract_features(
            sample_card_data, sample_market_data, sample_player_data
        )

        assert features.shape == (1, len(predictor.feature_names))
        assert features[0][0] == 2003  # year
        assert features[0][1] == 9.5  # grade

    def test_extract_features_rookie_card(self, predictor):
        """Test de detección de rookie card"""
        card_data = {"title": "2000 Topps Rookie Card", "year": 2000}
        market_data = {}
        player_data = {}

        features = predictor._extract_features(card_data, market_data, player_data)

        # El tercer feature (índice 2) es is_rookie_card
        assert features[0][2] == 1

    def test_extract_features_autograph(self, predictor):
        """Test de detección de autógrafo"""
        card_data = {"title": "2000 Topps Auto Signature", "year": 2000}
        market_data = {}
        player_data = {}

        features = predictor._extract_features(card_data, market_data, player_data)

        # El cuarto feature (índice 3) es is_autograph
        assert features[0][3] == 1

    def test_extract_features_patch(self, predictor):
        """Test de detección de patch"""
        card_data = {"title": "2000 Topps Game Used Patch", "year": 2000}
        market_data = {}
        player_data = {}

        features = predictor._extract_features(card_data, market_data, player_data)

        # El quinto feature (índice 4) es is_patch
        assert features[0][4] == 1

    def test_predict_without_training(
        self, predictor, sample_card_data, sample_market_data, sample_player_data
    ):
        """Test de predicción sin modelo entrenado"""
        result = predictor.predict(sample_card_data, sample_market_data, sample_player_data)

        assert isinstance(result, PredictionResult)
        assert result.predicted_price >= 0
        assert result.confidence == 0.5  # Baja confianza sin entrenamiento
        assert result.trend in ["up", "down", "stable"]
        assert result.model_version == "1.0.0"

    def test_predict_with_training(self, predictor):
        """Test de predicción con modelo entrenado"""
        # Crear datos de entrenamiento sintéticos
        np.random.seed(42)
        n_samples = 100

        data = pd.DataFrame(
            {
                "year": np.random.randint(1990, 2024, n_samples),
                "grade": np.random.uniform(5, 10, n_samples),
                "is_rookie_card": np.random.randint(0, 2, n_samples),
                "is_autograph": np.random.randint(0, 2, n_samples),
                "is_patch": np.random.randint(0, 2, n_samples),
                "is_parallel": np.random.randint(0, 2, n_samples),
                "card_number_normalized": np.random.uniform(0, 1, n_samples),
                "market_price_mean": np.random.uniform(50, 500, n_samples),
                "market_price_std": np.random.uniform(10, 100, n_samples),
                "market_volume_30d": np.random.randint(0, 50, n_samples),
                "market_trend_slope": np.random.uniform(-0.1, 0.1, n_samples),
                "player_performance_score": np.random.uniform(40, 100, n_samples),
                "player_sentiment_score": np.random.uniform(-1, 1, n_samples),
                "player_years_in_league": np.random.randint(1, 25, n_samples),
                "player_all_star_count": np.random.randint(0, 20, n_samples),
                "player_mvp_count": np.random.randint(0, 5, n_samples),
                "edition_size": np.random.uniform(0.3, 1.0, n_samples),
                "print_run": np.random.uniform(0.5, 1.0, n_samples),
                "sport_encoded": np.random.randint(0, 5, n_samples),
                "brand_encoded": np.random.randint(0, 5, n_samples),
                "sale_price": np.random.uniform(50, 1000, n_samples),
            }
        )

        # Entrenar modelo
        metrics = predictor.train(data)

        assert predictor.is_trained is True
        assert "r2_score" in metrics
        assert "mae" in metrics
        assert metrics["mae"] > 0

    def test_train_insufficient_data(self, predictor):
        """Test de entrenamiento con datos insuficientes"""
        # Crear DataFrame con pocas columnas
        data = pd.DataFrame(
            {
                "year": [2000, 2001, 2002],
                "price": [100, 200, 300],
            }
        )

        metrics = predictor.train(data)

        assert "error" in metrics
        assert predictor.is_trained is False

    def test_prediction_result_structure(
        self, predictor, sample_card_data, sample_market_data, sample_player_data
    ):
        """Test de estructura del resultado de predicción"""
        result = predictor.predict(sample_card_data, sample_market_data, sample_player_data)

        # Verificar que todos los campos requeridos están presentes
        assert hasattr(result, "predicted_price")
        assert hasattr(result, "confidence")
        assert hasattr(result, "trend")
        assert hasattr(result, "trend_percentage")
        assert hasattr(result, "price_range_low")
        assert hasattr(result, "price_range_high")
        assert hasattr(result, "factors")
        assert hasattr(result, "model_version")
        assert hasattr(result, "prediction_date")

        # Verificar tipos
        assert isinstance(result.predicted_price, (int, float))
        assert isinstance(result.confidence, float)
        assert isinstance(result.trend, str)
        assert isinstance(result.factors, list)
        assert isinstance(result.prediction_date, datetime)

    def test_prediction_factors(self, predictor):
        """Test de factores en la predicción"""
        # Tarjeta con grade alto
        card_data = {"title": "PSA 10 Gem Mint", "year": 2000, "grade": 10.0}
        market_data = {"trend_slope": 0.1}
        player_data = {"performance_score": 90}

        result = predictor.predict(card_data, market_data, player_data)

        # Verificar que hay factores
        assert len(result.factors) > 0

        # Buscar factor de grade
        grade_factor = next((f for f in result.factors if f["factor"] == "Grade Perfecto"), None)
        assert grade_factor is not None
        assert grade_factor["impact"] == "positive"

    def test_prediction_trend_up(self, predictor):
        """Test de tendencia positiva"""
        card_data = {}
        market_data = {"trend_slope": 0.1}
        player_data = {}

        result = predictor.predict(card_data, market_data, player_data)

        assert result.trend == "up"
        assert result.trend_percentage > 0

    def test_prediction_trend_down(self, predictor):
        """Test de tendencia negativa"""
        card_data = {}
        market_data = {"trend_slope": -0.1}
        player_data = {}

        result = predictor.predict(card_data, market_data, player_data)

        assert result.trend == "down"
        assert result.trend_percentage > 0

    def test_prediction_trend_stable(self, predictor):
        """Test de tendencia estable"""
        card_data = {}
        market_data = {"trend_slope": 0.0}
        player_data = {}

        result = predictor.predict(card_data, market_data, player_data)

        assert result.trend == "stable"
        assert result.trend_percentage == 0.0

    def test_price_range_calculation(self, predictor):
        """Test de cálculo del rango de precio"""
        card_data = {}
        market_data = {"trend_slope": 0.0}
        player_data = {}

        result = predictor.predict(card_data, market_data, player_data)

        # El precio predicho debe estar dentro del rango
        assert result.price_range_low <= result.predicted_price <= result.price_range_high
        # El rango bajo debe ser menor que el predicho
        assert result.price_range_low < result.predicted_price
        # El rango alto debe ser mayor que el predicho
        assert result.price_range_high > result.predicted_price

    def test_get_feature_importance(self, predictor):
        """Test de obtención de importancia de features"""
        # Sin entrenar
        importance = predictor.get_feature_importance()
        assert importance == {}

    def test_confidence_based_on_coefficient_of_variation(self, predictor):
        """Test de confidence basado en coeficiente de variación"""
        # Mercado con baja variación
        card_data = {}
        market_data_low_cv = {
            "price_mean": 500.0,
            "price_std": 25.0,  # CV = 0.05
            "trend_slope": 0.0,
        }
        player_data = {}

        result_low_cv = predictor.predict(card_data, market_data_low_cv, player_data)

        # Mercado con alta variación
        market_data_high_cv = {
            "price_mean": 500.0,
            "price_std": 200.0,  # CV = 0.4
            "trend_slope": 0.0,
        }

        result_high_cv = predictor.predict(card_data, market_data_high_cv, player_data)

        # Baja variación debe dar mayor confianza
        if predictor.is_trained:
            assert result_low_cv.confidence >= result_high_cv.confidence

    def test_random_forest_model(self):
        """Test de inicialización con Random Forest"""
        predictor = PricePredictor(model_type="random_forest")
        assert predictor.model_type == "random_forest"


class TestPredictionResult:
    """Tests para la clase PredictionResult"""

    def test_prediction_result_creation(self):
        """Test de creación de PredictionResult"""
        result = PredictionResult(
            predicted_price=500.0,
            confidence=0.85,
            trend="up",
            trend_percentage=5.0,
            price_range_low=400.0,
            price_range_high=600.0,
            factors=[{"factor": "Grade", "impact": "positive"}],
            model_version="1.0.0",
            prediction_date=datetime.now(),
        )

        assert result.predicted_price == 500.0
        assert result.confidence == 0.85
        assert result.trend == "up"
        assert result.factors[0]["factor"] == "Grade"


# Test de integración con datos sintéticos
@pytest.mark.integration
def test_model_training_integration():
    """Test de integración completo"""
    np.random.seed(42)
    n_samples = 200

    data = pd.DataFrame(
        {
            "year": np.random.randint(1990, 2024, n_samples),
            "grade": np.random.uniform(5, 10, n_samples),
            "is_rookie_card": np.random.randint(0, 2, n_samples),
            "is_autograph": np.random.randint(0, 2, n_samples),
            "is_patch": np.random.randint(0, 2, n_samples),
            "is_parallel": np.random.randint(0, 2, n_samples),
            "card_number_normalized": np.random.uniform(0, 1, n_samples),
            "market_price_mean": np.random.uniform(50, 500, n_samples),
            "market_price_std": np.random.uniform(10, 100, n_samples),
            "market_volume_30d": np.random.randint(0, 50, n_samples),
            "market_trend_slope": np.random.uniform(-0.1, 0.1, n_samples),
            "player_performance_score": np.random.uniform(40, 100, n_samples),
            "player_sentiment_score": np.random.uniform(-1, 1, n_samples),
            "player_years_in_league": np.random.randint(1, 25, n_samples),
            "player_all_star_count": np.random.randint(0, 20, n_samples),
            "player_mvp_count": np.random.randint(0, 5, n_samples),
            "edition_size": np.random.uniform(0.3, 1.0, n_samples),
            "print_run": np.random.uniform(0.5, 1.0, n_samples),
            "sport_encoded": np.random.randint(0, 5, n_samples),
            "brand_encoded": np.random.randint(0, 5, n_samples),
            # Target: precio basado en features con algo de ruido
            "sale_price": (
                100
                + 50 * np.random.uniform(5, 10, n_samples)  # grade effect
                + 200 * np.random.randint(0, 2, n_samples)  # rookie effect
                + 150 * np.random.randint(0, 2, n_samples)  # auto effect
                + np.random.uniform(50, 500, n_samples)  # market effect
            ),
        }
    )

    predictor = PricePredictor()
    metrics = predictor.train(data, test_size=0.2)

    assert metrics["r2_score"] > 0.3  # El modelo debe explicar al menos 30% de la varianza
    assert metrics["mae"] > 0
    assert predictor.is_trained is True

    # Hacer una predicción
    result = predictor.predict(
        {"year": 2000, "grade": 9.0},
        {"price_mean": 500, "price_std": 100, "trend_slope": 0.02},
        {"performance_score": 80},
    )

    assert result.predicted_price > 0
    assert result.confidence > 0.5
