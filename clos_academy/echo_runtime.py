"""Echo Runtime — warstwa Academy dla fazy ciszy (v0.9, na partial_step()).

Cel: obsłużyć fazę ciszy lekcji Pattern Echo BEZ modyfikacji Brain Runtime.
Do v0.8.2 (opcja B) ta warstwa ręcznie komponowała pojedyncze zamrożone
prymitywy Core (predict/compute_error/.../apply_decay), pomijając wyłącznie
perceive — duplikując kolejność kroków z BrainRuntime.step() poza Core, z
ryzykiem cichego rozjazdu przy przyszłej zmianie tej kolejności (patrz
docs/spec_partial_step.md, sekcja "Motywacja").

Od SPRINT_v0.9.md (Priorytet 3) ta duplikacja jest usunięta: silent_step()
deleguje do sankcjonowanego, addytywnego API —
BrainRuntime.partial_step(skip={PipelineStep.PERCEIVE}) — które komponuje
TE SAME prymitywy w TEJ SAMEJ kolejności, ale w jednym, jedynym miejscu
(clos_brain/brain_runtime.py), audytowalnym jako pojedynczy kontrakt Core.

To NIE jest kod poznawczy — to orkiestracja eksperymentu warstwy badawczej.
"""

from clos_brain.tissue import BrainTissue
from clos_brain.brain_runtime import BrainRuntime, PipelineStep


def silent_step(brain: BrainTissue, seed: int, tick: int) -> BrainTissue:
    """Jeden krok fazy ciszy — pipeline Core BEZ percepcji.

    Cienki wrapper nad BrainRuntime.partial_step(skip={PERCEIVE}): brak
    bodźca zewnętrznego w tym ticku (sensory_input=None), reszta pipeline'u
    (predict/compute_error/compute_precision/regulate/update_memory/
    apply_decay) identyczna jak w BrainRuntime.step().
    """
    return BrainRuntime.partial_step(
        brain, sensory_input=None, seed=seed, tick=tick, skip={PipelineStep.PERCEIVE}
    )
