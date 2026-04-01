from functools import cache
from typing import Any

from microsoft.graph import download_pptx_file_content
from microsoft.types import GraphDriveItem, GraphHeaders
from presentation_reader import extract_slide_text_from_pptx_bytes


class GeneratorRegistry:
    def __init__(self, *, drive_id: str, headers: GraphHeaders):
        self.drive_id = drive_id
        self.headers = headers

    @cache
    def get_slide_texts_for_item(self, item_id: str) -> tuple[str, ...]:
        pptx_bytes = download_pptx_file_content(self.drive_id, item_id, self.headers)
        return tuple(extract_slide_text_from_pptx_bytes(pptx_bytes))

    def identity_generator(self, source_key: str):
        def generate(item: GraphDriveItem) -> Any:
            return item[source_key]

        generate.is_ai = False
        return generate

    def slide_texts_generator(self):
        def generate(item: GraphDriveItem) -> list[str]:
            return list(self.get_slide_texts_for_item(item["id"]))

        generate.is_ai = False
        return generate

    def number_of_slides_generator(self):
        slide_texts = self.slide_texts_generator()

        def generate(item: GraphDriveItem) -> int:
            return len(slide_texts(item))

        generate.is_ai = False
        return generate

    def average_words_per_slide_generator(self):
        slide_texts = self.slide_texts_generator()

        def generate(item: GraphDriveItem) -> float:
            slides = slide_texts(item)
            if not slides:
                return 0.0
            return sum(len(slide.split()) for slide in slides) / len(slides)

        generate.is_ai = False
        return generate

    def ai_generator(self, field_name: str, output_type: Any, description: str):
        def generate(item: GraphDriveItem) -> None:
            return None

        generate.is_ai = True
        generate.field_name = field_name
        generate.output_type = output_type
        generate.description = description
        return generate
