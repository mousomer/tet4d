from __future__ import annotations

import unittest
from enum import IntEnum

from tet4d.engine.runtime.topology_playground_state import (
    TopologyPlaygroundGluingDraft,
)
from tet4d.engine.topology_explorer.domain_validation import (
    require_exact_bool,
    require_integral,
    require_integral_sequence,
    require_string,
)
from tet4d.engine.topology_explorer.glue_model import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    MoveStep,
)
from tet4d.engine.topology_explorer.transport_resolver import (
    ExplorerTransportFrameTransform,
)
from tet4d.generated.topology_contract_v1 import MAXIMUM_RANK, MINIMUM_RANK


class _IntegralValue(IntEnum):
    TWO = 2


def _valid_gluing(*, enabled: bool = True, glue_id: str = "wrap_x") -> GluingDescriptor:
    return GluingDescriptor(
        glue_id=glue_id,
        source=BoundaryRef(dimension=2, axis=0, side="-"),
        target=BoundaryRef(dimension=2, axis=0, side="+"),
        transform=BoundaryTransform(permutation=(0,), signs=(1,)),
        enabled=enabled,
    )


class TestTopologyDomainValidation(unittest.TestCase):
    def test_integral_policy_accepts_non_boolean_integrals_and_normalizes(self) -> None:
        self.assertEqual(require_integral(_IntegralValue.TWO, "value"), 2)
        self.assertIs(type(require_integral(_IntegralValue.TWO, "value")), int)

    def test_scalar_helpers_reject_lossy_or_cross_type_values(self) -> None:
        for value in (True, False, 2.0, 2.9, "2", None, [], {}):
            with self.subTest(integral=value), self.assertRaises(ValueError):
                require_integral(value, "value")
        for value in (0, 1, "false", "true", None, [], {}):
            with self.subTest(boolean=value), self.assertRaises(ValueError):
                require_exact_bool(value, "value")
        for value in (0, True, None, [], {}):
            with self.subTest(string=value), self.assertRaises(ValueError):
                require_string(value, "value")

    def test_integral_sequence_rejects_invalid_containers_and_members(self) -> None:
        for value in ("01", b"01", {"axis": 0}, (0, True), (0, 1.0), (0, "1")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_integral_sequence(value, "values")
        self.assertEqual(
            require_integral_sequence([0, _IntegralValue.TWO], "values"), (0, 2)
        )


class TestStrictTopologyDomainObjects(unittest.TestCase):
    def test_boundary_axis_rejects_non_integral_values(self) -> None:
        for value in (0.9, 1.0, True, False, "0", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                BoundaryRef(dimension=2, axis=value, side="-")  # type: ignore[arg-type]

    def test_boundary_dimension_and_side_are_strict(self) -> None:
        for value in (2.9, 2.0, "2", True, False, None):
            with self.subTest(dimension=value), self.assertRaises(ValueError):
                BoundaryRef(dimension=value, axis=0, side="-")  # type: ignore[arg-type]
        for value in (-1, 1, True, None, object()):
            with self.subTest(side=value), self.assertRaises(ValueError):
                BoundaryRef(dimension=2, axis=0, side=value)  # type: ignore[arg-type]

    def test_transform_permutation_entries_are_strict(self) -> None:
        for value in (0.9, 0.0, True, "0", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                BoundaryTransform(permutation=(value,), signs=(1,))  # type: ignore[arg-type]

    def test_transform_sign_entries_are_strict_unit_signs(self) -> None:
        for value in (1.8, 1.0, True, "1", 0, 2, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                BoundaryTransform(permutation=(0,), signs=(value,))  # type: ignore[arg-type]

    def test_transform_requires_supported_sequences_and_signed_permutation(
        self,
    ) -> None:
        invalid = (
            ("0", (1,)),
            ((0,), "1"),
            ((0, 0), (1, 1)),
            ((0, 1), (1,)),
        )
        for permutation, signs in invalid:
            with (
                self.subTest(permutation=permutation, signs=signs),
                self.assertRaises(ValueError),
            ):
                BoundaryTransform(permutation=permutation, signs=signs)  # type: ignore[arg-type]
        transform = BoundaryTransform(permutation=[1, 0], signs=[-1, 1])  # type: ignore[arg-type]
        self.assertEqual(transform.permutation, (1, 0))
        self.assertEqual(transform.signs, (-1, 1))

    def test_profile_dimension_rejects_lossy_values_and_uses_generated_limits(
        self,
    ) -> None:
        for value in (2.9, 2.0, "2", True, False, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ExplorerTopologyProfile(dimension=value, gluings=())  # type: ignore[arg-type]
        self.assertEqual(
            ExplorerTopologyProfile(MINIMUM_RANK, ()).dimension,
            MINIMUM_RANK,
        )
        self.assertEqual(
            ExplorerTopologyProfile(MAXIMUM_RANK, ()).dimension,
            MAXIMUM_RANK,
        )

    def test_profile_validates_gluing_members_before_tuple_storage(self) -> None:
        glue = _valid_gluing()
        profile = ExplorerTopologyProfile(dimension=2, gluings=[glue])  # type: ignore[arg-type]
        self.assertEqual(profile.gluings, (glue,))
        for value in ("glue", b"glue", {"glue": glue}, (glue, object())):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ExplorerTopologyProfile(dimension=2, gluings=value)  # type: ignore[arg-type]

    def test_gluing_id_enabled_and_owned_types_are_strict(self) -> None:
        for value in (0, 1, "false", "true", "TRUE", None, [], {}):
            with self.subTest(enabled=value), self.assertRaises(ValueError):
                _valid_gluing(enabled=value)  # type: ignore[arg-type]
        for value in (1, True, None, [], {}):
            with self.subTest(glue_id=value), self.assertRaises(ValueError):
                _valid_gluing(glue_id=value)  # type: ignore[arg-type]

    def test_move_axis_and_delta_reject_lossy_values(self) -> None:
        for value in (0.9, 1.9, 1.0, True, "1", None):
            with self.subTest(axis=value), self.assertRaises(ValueError):
                MoveStep(axis=value, delta=1)  # type: ignore[arg-type]
            with self.subTest(delta=value), self.assertRaises(ValueError):
                MoveStep(axis=0, delta=value)  # type: ignore[arg-type]
        for value in (0, 2, -2):
            with self.subTest(delta=value), self.assertRaises(ValueError):
                MoveStep(axis=0, delta=value)
        self.assertEqual(MoveStep(axis=_IntegralValue.TWO, delta=-1).axis, 2)

    def test_frame_transform_and_runtime_gluing_draft_do_not_reinterpret_values(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            ExplorerTransportFrameTransform(
                permutation=(0.0,),
                signs=(1,),
                translation=(0,),
            )
        draft = TopologyPlaygroundGluingDraft(enabled="false")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            draft.normalize(dimension=2)
        draft = TopologyPlaygroundGluingDraft(permutation=[], signs=[])  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            draft.normalize(dimension=2)


if __name__ == "__main__":
    unittest.main()
