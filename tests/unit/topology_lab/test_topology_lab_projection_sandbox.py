from __future__ import annotations

from types import SimpleNamespace
import unittest
import pygame

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)
from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.topology_lab import controls_panel as topology_lab_controls_panel
from tet4d.ui.pygame.topology_lab import projection_scene
from tet4d.ui.pygame.topology_lab import scene2d
from tet4d.ui.pygame.topology_lab.scene2d import draw_scene as draw_scene_2d
from tet4d.ui.pygame.topology_lab.scene3d import draw_scene as draw_scene_3d
from tet4d.ui.pygame.topology_lab.scene4d import draw_scene as draw_scene_4d


class TestTopologyLabProjectionSandbox(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    def _fonts(self):
        return SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )

    def _profile_3d(self) -> ExplorerTopologyProfile:
        return ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                GluingDescriptor(
                    glue_id="glue_001",
                    source=BoundaryRef(dimension=3, axis=0, side="-"),
                    target=BoundaryRef(dimension=3, axis=0, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                ),
            ),
        )

    def _profile_4d(self) -> ExplorerTopologyProfile:
        return ExplorerTopologyProfile(
            dimension=4,
            gluings=(
                GluingDescriptor(
                    glue_id="glue_001",
                    source=BoundaryRef(dimension=4, axis=0, side="-"),
                    target=BoundaryRef(dimension=4, axis=3, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1, 2), signs=(1, 1, 1)),
                ),
            ),
        )

    def test_projection_info_panel_uses_probe_label_for_probe_and_legacy_alias(self) -> None:
        self.assertEqual(
            projection_scene._mode_label_for_tool(topology_lab_menu.TOOL_PROBE),
            "Probe",
        )
        self.assertEqual(
            projection_scene._mode_label_for_tool("inspect_boundary"),
            "Probe",
        )

    def _assert_sandbox_cells_render(
        self,
        *,
        dimension: int,
        surface_size: tuple[int, int],
        area: pygame.Rect,
        preview_dims: tuple[int, ...],
        probe_coord: tuple[int, ...],
        sandbox_cells: tuple[tuple[int, ...], ...],
    ) -> None:
        fonts = self._fonts()
        profile = self._profile_3d() if dimension == 3 else self._profile_4d()
        boundaries = tuple(
            BoundaryRef(dimension=dimension, axis=axis, side=side)
            for axis in range(dimension)
            for side in ("-", "+")
        )
        control = pygame.Surface(surface_size)
        rendered = pygame.Surface(surface_size)
        draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
        common_kwargs = dict(
            area=area,
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[-1],
            active_glue_ids={boundary.label: "free" for boundary in boundaries},
            basis_arrows=(),
            preview_dims=preview_dims,
            profile=profile,
            active_tool="piece_sandbox",
            probe_coord=probe_coord,
        )
        draw_scene(control, fonts, **common_kwargs)
        hits = draw_scene(rendered, fonts, **common_kwargs, sandbox_cells=sandbox_cells)
        target = next(
            hit
            for hit in hits
            if hit.kind == "projection_cell" and hit.value == sandbox_cells[0]
        )
        self.assertNotEqual(
            rendered.get_at(target.rect.center),
            control.get_at(target.rect.center),
        )

    def _assert_projection_overlay_projects_hidden_slices(
        self,
        *,
        dimension: int,
        surface_size: tuple[int, int],
        area: pygame.Rect,
        preview_dims: tuple[int, ...],
        probe_coord: tuple[int, ...],
        target_value: tuple[int, ...],
        extra_kwargs: dict[str, object],
    ) -> None:
        fonts = self._fonts()
        profile = self._profile_3d() if dimension == 3 else self._profile_4d()
        boundaries = tuple(
            BoundaryRef(dimension=dimension, axis=axis, side=side)
            for axis in range(dimension)
            for side in ("-", "+")
        )
        control = pygame.Surface(surface_size)
        rendered = pygame.Surface(surface_size)
        draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
        common_kwargs = dict(
            area=area,
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[-1],
            active_glue_ids={boundary.label: "free" for boundary in boundaries},
            basis_arrows=(),
            preview_dims=preview_dims,
            profile=profile,
            active_tool="piece_sandbox",
            probe_coord=probe_coord,
        )
        merged_kwargs = dict(common_kwargs)
        merged_kwargs.update(extra_kwargs)
        control_hits = draw_scene(control, fonts, **common_kwargs)
        draw_scene(rendered, fonts, **merged_kwargs)
        target = next(
            hit
            for hit in control_hits
            if hit.kind == "projection_cell" and hit.value == target_value
        )
        self.assertNotEqual(
            rendered.get_at(target.rect.center),
            control.get_at(target.rect.center),
        )

    def test_sandbox_cells_render_in_projection_panels(self) -> None:
        for params in (
            dict(
                dimension=3,
                surface_size=(960, 760),
                area=pygame.Rect(40, 80, 620, 360),
                preview_dims=(4, 5, 3),
                probe_coord=(0, 2, 1),
                sandbox_cells=((1, 2, 1), (2, 2, 1)),
            ),
            dict(
                dimension=4,
                surface_size=(1100, 820),
                area=pygame.Rect(40, 80, 760, 420),
                preview_dims=(3, 4, 5, 2),
                probe_coord=(0, 2, 3, 0),
                sandbox_cells=((1, 2, 3, 0), (2, 2, 3, 0)),
            ),
        ):
            with self.subTest(dimension=params["dimension"]):
                self._assert_sandbox_cells_render(**params)

    def test_sandbox_cells_remain_visible_when_hidden_slices_differ(self) -> None:
        for params in (
            dict(
                dimension=3,
                surface_size=(960, 760),
                area=pygame.Rect(40, 80, 620, 360),
                preview_dims=(4, 5, 4),
                probe_coord=(0, 2, 0),
                target_value=(1, 2, 0),
                extra_kwargs={"sandbox_cells": ((1, 2, 3), (2, 2, 3))},
            ),
            dict(
                dimension=4,
                surface_size=(1100, 820),
                area=pygame.Rect(40, 80, 760, 420),
                preview_dims=(3, 4, 5, 3),
                probe_coord=(0, 2, 0, 0),
                target_value=(1, 2, 0, 0),
                extra_kwargs={"sandbox_cells": ((1, 2, 4, 2), (2, 2, 4, 2))},
            ),
        ):
            with self.subTest(dimension=params["dimension"]):
                self._assert_projection_overlay_projects_hidden_slices(**params)

    def test_probe_trace_projects_across_hidden_slices_in_4d(self) -> None:
        self._assert_projection_overlay_projects_hidden_slices(
            dimension=4,
            surface_size=(1100, 820),
            area=pygame.Rect(40, 80, 760, 420),
            preview_dims=(3, 4, 5, 3),
            probe_coord=(0, 0, 0, 0),
            target_value=(1, 2, 0, 0),
            extra_kwargs={
                "active_tool": topology_lab_menu.TOOL_PROBE,
                "probe_path": ((1, 2, 4, 2), (2, 2, 4, 2)),
            },
        )

    def test_neighbor_markers_render_as_dots_without_link_lines_in_2d(self) -> None:
        surface = pygame.Surface((720, 520))
        control = pygame.Surface((720, 520))
        fonts = self._fonts()
        area = pygame.Rect(40, 80, 360, 280)
        boundaries = tuple(
            BoundaryRef(dimension=2, axis=axis, side=side)
            for axis in range(2)
            for side in ("-", "+")
        )
        common_kwargs = dict(
            area=area,
            boundaries=boundaries,
            source_boundary=boundaries[0],
            target_boundary=boundaries[1],
            active_glue_ids={boundary.label: "free" for boundary in boundaries},
            basis_arrows=(),
            preview_dims=(5, 4),
            probe_coord=(0, 0),
        )
        draw_scene_2d(control, fonts, **common_kwargs)
        draw_scene_2d(
            surface,
            fonts,
            **common_kwargs,
            neighbor_markers=((1, 1), (3, 1)),
        )
        board, cell_size = scene2d._board_rect(area, (5, 4))
        marker_center = scene2d._cell_rect(board, cell_size, (1, 1)).center
        midpoint = scene2d._cell_rect(board, cell_size, (2, 1)).center
        self.assertNotEqual(surface.get_at(marker_center), control.get_at(marker_center))
        self.assertEqual(surface.get_at(midpoint), control.get_at(midpoint))

    def test_neighbor_markers_project_across_hidden_slices_in_3d_and_4d(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, marker_coord in (
            (3, (960, 760), pygame.Rect(40, 80, 620, 360), (4, 5, 4), (0, 2, 0), (1, 2, 3)),
            (4, (1100, 820), pygame.Rect(40, 80, 760, 420), (3, 4, 5, 3), (0, 2, 0, 0), (1, 2, 4, 2)),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                control.fill((0, 0, 0))
                rendered.fill((0, 0, 0))
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool=topology_lab_menu.TOOL_PROBE,
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    neighbor_markers=(marker_coord,),
                )
                panels, _info_rect = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                marker_center = projection_scene._cell_rect(
                    board_rect,
                    cell_size,
                    (1, 2),
                ).center
                changed = False
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        point = (marker_center[0] + dx, marker_center[1] + dy)
                        if rendered.get_at(point) != control.get_at(point):
                            changed = True
                            break
                    if changed:
                        break
                self.assertTrue(changed)

    def test_nd_neighbor_markers_do_not_drop_early_cells_when_many_are_visible(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, marker_coords, expected_pairs in (
            (
                3,
                (960, 760),
                pygame.Rect(40, 80, 620, 360),
                (5, 5, 5),
                (2, 2, 2),
                (
                    (0, 2, 2),
                    (4, 2, 2),
                    (2, 0, 2),
                    (2, 4, 2),
                    (1, 2, 2),
                    (3, 2, 2),
                    (2, 1, 2),
                    (2, 3, 2),
                    (1, 1, 2),
                    (3, 1, 2),
                    (1, 3, 2),
                    (3, 3, 2),
                    (0, 1, 2),
                    (4, 3, 2),
                ),
                ((0, 2), (4, 2), (2, 0), (2, 4)),
            ),
            (
                4,
                (1100, 820),
                pygame.Rect(40, 80, 760, 420),
                (5, 5, 5, 5),
                (2, 2, 2, 2),
                (
                    (0, 2, 2, 2),
                    (4, 2, 2, 2),
                    (2, 0, 2, 2),
                    (2, 4, 2, 2),
                    (1, 2, 2, 2),
                    (3, 2, 2, 2),
                    (2, 1, 2, 2),
                    (2, 3, 2, 2),
                    (1, 1, 2, 2),
                    (3, 1, 2, 2),
                    (1, 3, 2, 2),
                    (3, 3, 2, 2),
                    (0, 1, 2, 2),
                    (4, 3, 2, 2),
                ),
                ((0, 2), (4, 2), (2, 0), (2, 4)),
            ),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="piece_sandbox",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    neighbor_markers=marker_coords,
                )
                panels, _ = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                for pair in expected_pairs:
                    point = projection_scene._cell_rect(board_rect, cell_size, pair).center
                    self.assertNotEqual(
                        rendered.get_at(point),
                        control.get_at(point),
                    )

    def test_sandbox_mode_without_neighbor_markers_does_not_paint_neighbor_cells_in_nd(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, sandbox_cells, empty_pair in (
            (3, (960, 760), pygame.Rect(40, 80, 620, 360), (4, 5, 4), (2, 2, 2), ((2, 2, 2), (3, 2, 2), (2, 3, 2), (2, 2, 3)), (1, 2)),
            (4, (1100, 820), pygame.Rect(40, 80, 760, 420), (4, 5, 5, 4), (2, 2, 2, 2), ((2, 2, 2, 2), (3, 2, 2, 2), (2, 3, 2, 2), (2, 2, 3, 2), (2, 2, 2, 3)), (1, 2)),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                control.fill((0, 0, 0))
                rendered.fill((0, 0, 0))
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="piece_sandbox",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    sandbox_cells=sandbox_cells,
                    neighbor_markers=(),
                )
                panels, _info_rect = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                target_rect = projection_scene._cell_rect(board_rect, cell_size, empty_pair)
                self.assertEqual(
                    rendered.get_at(target_rect.center),
                    control.get_at(target_rect.center),
                )

    def test_nd_sandbox_cells_render_as_boxes_not_center_dots(self) -> None:
        fonts = self._fonts()
        for dimension, surface_size, area, preview_dims, probe_coord, sandbox_cells in (
            (
                3,
                (960, 760),
                pygame.Rect(40, 80, 620, 360),
                (4, 5, 4),
                (2, 2, 2),
                ((2, 2, 2), (3, 2, 2)),
            ),
            (
                4,
                (1100, 820),
                pygame.Rect(40, 80, 760, 420),
                (4, 5, 5, 4),
                (2, 2, 2, 2),
                ((2, 2, 2, 2), (3, 2, 2, 2)),
            ),
        ):
            with self.subTest(dimension=dimension):
                profile = self._profile_3d() if dimension == 3 else self._profile_4d()
                boundaries = tuple(
                    BoundaryRef(dimension=dimension, axis=axis, side=side)
                    for axis in range(dimension)
                    for side in ("-", "+")
                )
                control = pygame.Surface(surface_size)
                rendered = pygame.Surface(surface_size)
                draw_scene = draw_scene_3d if dimension == 3 else draw_scene_4d
                common_kwargs = dict(
                    area=area,
                    boundaries=boundaries,
                    source_boundary=boundaries[0],
                    target_boundary=boundaries[-1],
                    active_glue_ids={boundary.label: "free" for boundary in boundaries},
                    basis_arrows=(),
                    preview_dims=preview_dims,
                    profile=profile,
                    active_tool="piece_sandbox",
                    probe_coord=probe_coord,
                )
                draw_scene(control, fonts, **common_kwargs)
                draw_scene(
                    rendered,
                    fonts,
                    **common_kwargs,
                    sandbox_cells=sandbox_cells,
                )
                panels, _ = projection_scene._layout_projection_panels(
                    area,
                    dimension=dimension,
                    header_height=(70 if dimension == 4 else 64) + 10,
                )
                xy_panel = next(panel for panel in panels if panel.axes == (0, 1))
                board_rect, cell_size = projection_scene._panel_grid_rect(
                    xy_panel.rect,
                    preview_dims,
                    (0, 1),
                )
                target_rect = projection_scene._cell_rect(board_rect, cell_size, (3, 2))
                edge_point = (target_rect.x + 2, target_rect.centery)
                upper_edge_point = (target_rect.centerx, target_rect.y + 2)
                self.assertNotEqual(
                    rendered.get_at(edge_point),
                    control.get_at(edge_point),
                )
                self.assertNotEqual(
                    rendered.get_at(upper_edge_point),
                    control.get_at(upper_edge_point),
                )


class TestTopologyLabWorkspaceShell(unittest.TestCase):
    def _explorer_state(self, dimension: int) -> topology_lab_menu._TopologyLabState:
        profile = default_topology_profile_state(
            dimension=dimension,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        tangent_dimension = dimension - 1
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=dimension,
            profile=profile,
            explorer_profile=ExplorerTopologyProfile(dimension=dimension, gluings=()),
            explorer_draft=topology_lab_menu.ExplorerGlueDraft(
                slot_index=0,
                source_index=0,
                target_index=1,
                permutation_index=0,
                signs=tuple(1 for _ in range(tangent_dimension)),
            ),
        )
        topology_lab_menu._normalize_explorer_draft(state)
        state.active_pane = topology_lab_menu.PANE_SCENE
        return state

    def test_helper_lines_scaffold_editor_workspace(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)

        lines = topology_lab_menu._hint_lines_for_state(state)

        self.assertTrue(any("Editor workspace:" in line for line in lines))
        self.assertTrue(any("probe/selection only" in line for line in lines))

    def test_helper_lines_scaffold_sandbox_workspace_with_explicit_neighbor_state(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)

        lines = topology_lab_menu._hint_lines_for_state(state)

        self.assertTrue(any("Sandbox workspace:" in line for line in lines))
        self.assertTrue(any("Sandbox Neighbors:" in line for line in lines))

    def test_helper_lines_scaffold_play_workspace(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)

        lines = topology_lab_menu._hint_lines_for_state(state)

        self.assertTrue(any("Play workspace:" in line for line in lines))
        self.assertTrue(any("canonical gameplay runtime" in line for line in lines))

    def test_sandbox_neighbor_toggle_action_updates_canonical_state_explicitly(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)

        self.assertTrue(
            topology_lab_controls_panel._sandbox_neighbor_search_enabled(state)
        )
        topology_lab_menu._activate_action(state, "sandbox_neighbor_search")
        assert state.canonical_state is not None
        self.assertFalse(state.canonical_state.sandbox_piece_state.neighbor_search_enabled)

    def test_helper_lines_expose_unified_shell_and_vertical_keys_for_nd(self) -> None:
        state = self._explorer_state(4)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertIn(
            "Explorer Playground keeps presets, board size, seam editing, sandbox, and play on one screen.",
            lines,
        )
        self.assertIn(
            "Graphical explorer is the primary editor; Analysis View is optional secondary research and diagnostics.",
            lines,
        )
        self.assertTrue(any(line.startswith("Move Y:") for line in lines))
        self.assertIn(
            "Analysis view (secondary): adjust settings, workspace-owned contextual controls, and Save/Export/Experiments/Back here   Status rows only report the current seam context",
            lines,
        )

    def test_editor_trace_action_toggles_trace_without_hiding_probe(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)

        self.assertTrue(topology_lab_menu._probe_trace_visible(state))
        self.assertNotIn(
            ("editor_trace", "Hide Trace"),
            topology_lab_menu._action_buttons_for_state(state),
        )

    def test_draw_menu_keeps_editor_trace_as_controls_row_not_scene_action(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((1280, 900))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)
        topology_lab_menu._draw_menu(screen, fonts, state)

        row_hits = [
            hit
            for hit in state.mouse_targets
            if hit.kind == "row_select" and hit.value == "editor_trace"
        ]
        action_hits = [
            hit
            for hit in state.mouse_targets
            if hit.kind == "action" and hit.value == "editor_trace"
        ]

        self.assertEqual(len(row_hits), 1)
        self.assertFalse(action_hits)
        self.assertGreater(row_hits[0].rect.width, 300)
        self.assertLess(row_hits[0].rect.bottom, screen.get_height())

    def test_draw_menu_keeps_neighbors_as_controls_row_not_scene_action(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((1280, 900))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu._draw_menu(screen, fonts, state)

        row_hits = [
            hit
            for hit in state.mouse_targets
            if hit.kind == "row_select" and hit.value == "sandbox_neighbor_search"
        ]
        action_hits = [
            hit
            for hit in state.mouse_targets
            if hit.kind == "action" and hit.value == "sandbox_neighbor_search"
        ]

        self.assertEqual(len(row_hits), 1)
        self.assertFalse(action_hits)
        self.assertGreater(row_hits[0].rect.width, 300)
        self.assertLess(row_hits[0].rect.bottom, screen.get_height())

    def test_sandbox_neighbor_toggle_computes_real_neighbor_cells(self) -> None:
        state = self._explorer_state(2)
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(8, 8)),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.origin = (2, 2)
        state.sandbox.local_blocks = ((0, 0), (1, 0))
        topology_lab_menu._select_sandbox_projection_coord(state, (2, 2))

        markers = set(topology_lab_menu._active_workspace_neighbor_markers(state))

        self.assertEqual(markers, {(1, 2), (4, 2), (2, 1), (3, 1), (2, 3), (3, 3)})
        state.sandbox.neighbor_search_enabled = False
        self.assertEqual(topology_lab_menu._active_workspace_neighbor_markers(state), [])

    def test_workspace_preview_lines_include_sandbox_seam_crossings(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.seam_crossings = ["wrap_0: x+ -> x-"]
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            preview={
                "movement_graph": {
                    "cell_count": 1,
                    "directed_edge_count": 0,
                    "boundary_traversal_count": 0,
                    "component_count": 1,
                },
                "warnings": (),
                "sample_boundary_traversals": (),
            },
            preview_error=None,
        )
        self.assertIn("Seam crossings", lines)
        self.assertTrue(any("wrap_0: x+ -> x-" in line for line in lines))

    def test_hint_lines_expose_generated_pane_and_projection_contract(self) -> None:
        state = self._explorer_state(4)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertIn(
            "Explorer Playground keeps presets, board size, seam editing, sandbox, and play on one screen.",
            lines,
        )
        self.assertIn(
            "Pane: Analysis View   Tab/Shift+Tab switch pane   E/I choose Editor tool   B Sandbox   P Play   Enter plays from Play",
            lines,
        )
        self.assertIn(
            "Analysis view (secondary): adjust settings, workspace-owned contextual controls, and Save/Export/Experiments/Back here   Status rows only report the current seam context",
            lines,
        )
        self.assertTrue(any(line.startswith("Projection sync:") for line in lines))

    def test_hint_lines_change_for_scene_pane(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_SCENE
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertTrue(
            any(
                line.startswith("Explorer workspace (primary): the right-side helper")
                for line in lines
            )
        )

    def test_sandbox_hint_lines_restore_space_as_next_piece(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertIn(
            "Sandbox tool: movement keys and the footer grid move the piece, gameplay rotation keys rotate it, Space or ] next piece, [ previous piece, 0 resets",
            lines,
        )


if __name__ == "__main__":
    unittest.main()
