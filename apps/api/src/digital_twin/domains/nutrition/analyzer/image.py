"""
Image-Based Food Analysis

Uses Gemini Vision API to detect and identify foods from photos.
This is the AI-powered food recognition system.

Capabilities:
- Detect multiple foods in a single image
- Estimate portions
- Identify ingredients
- Detect food categories

Integration:
- Uses LLMFactory for model access
- Connects to core Vision agent for image processing

@module ImageFoodAnalyzer
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import base64

from ..schema import FoodEntry, FoodCategory, NutrientProfile

logger = logging.getLogger(__name__)


# =============================================================================
# RESULT TYPES
# =============================================================================

@dataclass
class DetectedFood:
    """A single food item detected in an image."""
    name: str
    category: FoodCategory = FoodCategory.UNKNOWN
    portion_estimate: str = "1 serving"
    portion_grams: float = 100.0
    confidence: float = 0.0
    bounding_box: Optional[Dict[str, float]] = None  # x, y, width, height
    ingredients: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "portion_estimate": self.portion_estimate,
            "portion_grams": self.portion_grams,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box,
            "ingredients": self.ingredients,
        }


@dataclass
class FoodDetectionResult:
    """Result of image-based food detection."""
    success: bool = True
    error: Optional[str] = None
    
    # Detected foods
    foods: List[FoodEntry] = field(default_factory=list)
    
    # Raw detection data
    raw_detections: List[DetectedFood] = field(default_factory=list)
    
    # Analysis metadata
    confidence: float = 0.0
    processing_time_ms: int = 0
    model_used: str = ""
    
    # Image info
    image_dimensions: Optional[Dict[str, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error": self.error,
            "foods": [f.to_dict() for f in self.foods],
            "raw_detections": [d.to_dict() for d in self.raw_detections],
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used,
        }


# =============================================================================
# IMAGE ANALYZER
# =============================================================================

class ImageFoodAnalyzer:
    """
    AI-powered food image analyzer.
    
    Uses Gemini Vision to:
    1. Detect foods in images
    2. Estimate portions
    3. Identify ingredients
    4. Categorize foods
    
    Example:
        analyzer = ImageFoodAnalyzer()
        result = await analyzer.analyze(image_bytes, "jpeg")
        for food in result.foods:
            print(f"Detected: {food.name} ({food.category})")
    """
    
    # System prompt for food detection
    FOOD_DETECTION_PROMPT = """You are a nutrition AI assistant specialized in food recognition.

Analyze this food image and identify all visible food items.

For each food item, provide:
1. name: The specific name of the food
2. category: One of [protein, vegetable, fruit, grain, dairy, fat, sugar, beverage, processed, mixed]
3. portion_estimate: Human-readable portion (e.g., "1 cup", "2 slices", "1 medium")
4. portion_grams: Estimated weight in grams
5. confidence: How confident you are (0.0 to 1.0)
6. ingredients: List of main ingredients if it's a prepared dish

Respond with a JSON object like:
{
    "foods": [
        {
            "name": "grilled chicken breast",
            "category": "protein",
            "portion_estimate": "1 medium breast",
            "portion_grams": 170,
            "confidence": 0.9,
            "ingredients": ["chicken"]
        }
    ],
    "meal_type": "dinner",
    "overall_assessment": "balanced meal with good protein"
}

If no food is detected, return {"foods": [], "error": "No food detected"}
"""
    
    def __init__(self):
        self._model_name = "gemini-2.5-flash"  # Fast model for image analysis
        self._llm = None
    
    async def _get_llm(self):
        """Get LLM instance lazily."""
        if self._llm is None:
            try:
                from .....core.llm_factory import LLMFactory
                factory = LLMFactory()
                self._llm = await factory.get_llm(self._model_name)
            except ImportError:
                logger.warning("[ImageFoodAnalyzer] LLMFactory not available, using placeholder")
                self._llm = None
        return self._llm
    
    async def analyze(
        self,
        image_data: bytes,
        image_type: str = "jpeg"
    ) -> FoodDetectionResult:
        """
        Analyze a food image.
        
        Args:
            image_data: Raw image bytes
            image_type: Image format (jpeg, png)
        
        Returns:
            FoodDetectionResult with detected foods
        """
        start_time = datetime.now()
        
        try:
            llm = await self._get_llm()
            
            if llm is None:
                # Placeholder response for when LLM not available
                return self._placeholder_response()
            
            # Encode image for API
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            
            # Call vision model
            response = await self._call_vision_model(llm, image_b64, image_type)
            
            # Parse response
            result = self._parse_response(response)
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result.processing_time_ms = processing_time
            result.model_used = self._model_name
            
            return result
            
        except Exception as e:
            logger.error(f"[ImageFoodAnalyzer] Error analyzing image: {e}")
            return FoodDetectionResult(
                success=False,
                error=str(e),
                processing_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )
    
    async def _call_vision_model(
        self,
        llm,
        image_b64: str,
        image_type: str
    ) -> str:
        """Call the vision model with the image."""
        # This would use the actual LLM with vision capabilities
        # For now, return a placeholder
        # Real implementation would use LangChain's multimodal message format
        
        from langchain_core.messages import HumanMessage
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": self.FOOD_DETECTION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_type};base64,{image_b64}"
                    }
                }
            ]
        )
        
        response = await llm.ainvoke([message])
        return response.content
    
    def _parse_response(self, response: str) -> FoodDetectionResult:
        """Parse LLM response into structured result."""
        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                return FoodDetectionResult(
                    success=False,
                    error="Could not parse response"
                )
            
            data = json.loads(response[json_start:json_end])
            
            if "error" in data:
                return FoodDetectionResult(
                    success=False,
                    error=data["error"]
                )
            
            # Convert detected foods to FoodEntry objects
            foods = []
            raw_detections = []
            total_confidence = 0.0
            
            for food_data in data.get("foods", []):
                # Create raw detection
                detection = DetectedFood(
                    name=food_data.get("name", "Unknown"),
                    category=self._parse_category(food_data.get("category", "unknown")),
                    portion_estimate=food_data.get("portion_estimate", "1 serving"),
                    portion_grams=food_data.get("portion_grams", 100),
                    confidence=food_data.get("confidence", 0.5),
                    ingredients=food_data.get("ingredients", []),
                )
                raw_detections.append(detection)
                
                # Create FoodEntry
                food_entry = FoodEntry(
                    name=detection.name,
                    category=detection.category,
                    quantity=1.0,
                    quantity_unit=detection.portion_estimate,
                    source="image",
                    confidence=detection.confidence,
                    nutrients=NutrientProfile(
                        serving_size=detection.portion_grams,
                        serving_unit="g",
                    ),
                )
                foods.append(food_entry)
                total_confidence += detection.confidence
            
            avg_confidence = total_confidence / len(foods) if foods else 0.0
            
            return FoodDetectionResult(
                success=True,
                foods=foods,
                raw_detections=raw_detections,
                confidence=avg_confidence,
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"[ImageFoodAnalyzer] JSON parse error: {e}")
            return FoodDetectionResult(
                success=False,
                error=f"JSON parse error: {e}"
            )
    
    def _parse_category(self, category_str: str) -> FoodCategory:
        """Parse category string to enum."""
        category_map = {
            "protein": FoodCategory.PROTEIN,
            "vegetable": FoodCategory.VEGETABLE,
            "fruit": FoodCategory.FRUIT,
            "grain": FoodCategory.GRAIN,
            "dairy": FoodCategory.DAIRY,
            "fat": FoodCategory.FAT,
            "sugar": FoodCategory.SUGAR,
            "beverage": FoodCategory.BEVERAGE,
            "processed": FoodCategory.PROCESSED,
            "mixed": FoodCategory.MIXED,
        }
        return category_map.get(category_str.lower(), FoodCategory.UNKNOWN)
    
    def _placeholder_response(self) -> FoodDetectionResult:
        """Return placeholder when LLM not available."""
        return FoodDetectionResult(
            success=True,
            foods=[
                FoodEntry(
                    name="Sample Food",
                    category=FoodCategory.MIXED,
                    quantity=1.0,
                    quantity_unit="serving",
                    source="placeholder",
                    confidence=0.5,
                )
            ],
            confidence=0.5,
            model_used="placeholder",
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def analyze_food_image(
    image_data: bytes,
    image_type: str = "jpeg"
) -> FoodDetectionResult:
    """
    Convenience function to analyze a food image.
    
    Creates an analyzer instance and runs analysis.
    """
    analyzer = ImageFoodAnalyzer()
    return await analyzer.analyze(image_data, image_type)
