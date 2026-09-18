from pydantic import BaseModel, Field

from fcf.domain.enums import STAGE_BY_KIND, AssetKind, Channel, Stage


class PromptSet(BaseModel):
    system: str | None = None
    user: str
    negative: str | None = None
    refs: list[str] = Field(default_factory=list)
    params: dict = Field(default_factory=dict)


class AssetSpec(BaseModel):
    key: str
    kind: AssetKind
    channel: Channel
    variant: str = "a"
    locale: str = "en"
    prompt: PromptSet | None = None
    depends_on: list[str] = Field(default_factory=list)
    provider: str | None = None

    @property
    def stage(self) -> Stage:
        return STAGE_BY_KIND[self.kind]


class ContentPlan(BaseModel):
    specs: list[AssetSpec]
    concept: str | None = None

    def by_stage(self, stage: Stage, only: set[str] | None = None) -> list[AssetSpec]:
        return [
            s
            for s in self.specs
            if s.stage == stage and (only is None or s.key in only)
        ]
