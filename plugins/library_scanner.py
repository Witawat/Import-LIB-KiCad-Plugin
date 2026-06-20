from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if not getattr(sys, 'frozen', False):
    current_dir = Path(__file__).resolve().parent
    kiutils_src = current_dir / "kiutils" / "src"
    if str(kiutils_src) not in sys.path:
        sys.path.insert(0, str(kiutils_src))

try:
    from kiutils.symbol import SymbolLib  # noqa: E402

    _HAS_KIUTILS = True
except ImportError:
    _HAS_KIUTILS = False

logger = logging.getLogger(__name__)


@dataclass
class SymbolEntry:
    lib_name: str
    file_path: Path
    symbol_names: list[str] = field(default_factory=list)
    file_size_kb: float = 0.0


@dataclass
class FootprintEntry:
    lib_name: str
    dir_path: Path
    footprint_names: list[str] = field(default_factory=list)
    file_count: int = 0


@dataclass
class ModelEntry:
    lib_name: str
    dir_path: Path
    model_files: list[dict[str, Any]] = field(default_factory=list)


class LibraryScanner:
    SUPPORTED_SOURCES = ["Octopart", "Samacsys", "UltraLibrarian", "Snapeda", "EasyEDA"]

    def __init__(self, dest_path: str | Path) -> None:
        self.dest_path = Path(dest_path)
        logger.info(f"LibraryScanner: dest_path={self.dest_path}, _HAS_KIUTILS={_HAS_KIUTILS}")

    def _detect_source(self, lib_name: str) -> str:
        for src in self.SUPPORTED_SOURCES:
            if src.lower() in lib_name.lower():
                return src
        return "Unknown"

    def scan_symbols(self) -> list[SymbolEntry]:
        results: list[SymbolEntry] = []
        if not self.dest_path.is_dir():
            logger.warning(f"scan_symbols: dest_path does not exist: {self.dest_path}")
            return results
        logger.info(f"scan_symbols: scanning {self.dest_path}")
        for f in sorted(self.dest_path.iterdir()):
            if f.is_file() and f.suffix == ".kicad_sym":
                entry = SymbolEntry(
                    lib_name=f.stem,
                    file_path=f,
                    file_size_kb=round(f.stat().st_size / 1024, 1),
                )
                names = self._read_symbol_names(f)
                if names:
                    entry.symbol_names = names
                results.append(entry)
                _0_1_entries = [n for n in names if "_0_" in n]
                logger.info(f"scan_symbols: found {f.name}: {len(names)} symbols, _0_1_count={len(_0_1_entries)}")
                if _0_1_entries:
                    logger.warning(f"scan_symbols: _0_1 entries in {f.name}: {_0_1_entries}")
        logger.info(f"scan_symbols: total libraries={len(results)}, total symbols={sum(len(r.symbol_names) for r in results)}")
        return results

    def _read_symbol_names(self, file_path: Path) -> list[str]:
        if _HAS_KIUTILS:
            for enc in ('utf-8', None, 'cp1252'):
                try:
                    lib = SymbolLib().from_file(str(file_path), encoding=enc)
                    names = [s.entryName for s in lib.symbols]
                    logger.debug(f"_read_symbol_names (kiutils, enc={enc}): {file_path.name} -> {len(names)} symbols")
                    return names
                except Exception as e:
                    logger.debug(f"Cannot read {file_path.name} with kiutils (enc={enc}): {e}")
            logger.info(f"_read_symbol_names: kiutils failed for {file_path.name}, falling back to regex")
        else:
            logger.debug(f"_read_symbol_names: kiutils not available, using regex for {file_path.name}")
        return self._read_symbol_names_regex(file_path)

    def _read_symbol_names_regex(self, file_path: Path) -> list[str]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            names = re.findall(r'\(symbol\s+"([^"]*)"', content)
            logger.debug(f"_read_symbol_names_regex: {file_path.name} -> {len(names)} symbols")
            return names
        except Exception as e:
            logger.debug(f"Cannot parse {file_path.name}: {e}")
            return []

    def scan_footprints(self) -> list[FootprintEntry]:
        results: list[FootprintEntry] = []
        if not self.dest_path.is_dir():
            logger.warning(f"scan_footprints: dest_path does not exist: {self.dest_path}")
            return results
        logger.info(f"scan_footprints: scanning {self.dest_path}")
        for d in sorted(self.dest_path.iterdir()):
            if d.is_dir() and d.suffix == ".pretty":
                mods = sorted(d.glob("*.kicad_mod"))
                names: list[str] = []
                for m in mods:
                    name = self._extract_footprint_name(m)
                    if name:
                        names.append(name)
                    else:
                        names.append(m.stem)
                results.append(
                    FootprintEntry(
                        lib_name=d.stem.replace(".pretty", ""),
                        dir_path=d,
                        footprint_names=names,
                        file_count=len(mods),
                    )
                )
                logger.info(f"scan_footprints: found {d.name}: {len(mods)} footprints")
        return results

    def _extract_footprint_name(self, file_path: Path) -> str | None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'\((?:module|footprint)\s+"([^"]*)"', content)
            if m:
                return m.group(1)
        except Exception as e:
            logger.debug(f"Cannot read {file_path.name}: {e}")
        return None

    def scan_models(self) -> list[ModelEntry]:
        results: list[ModelEntry] = []
        if not self.dest_path.is_dir():
            return results
        for d in sorted(self.dest_path.iterdir()):
            if d.is_dir() and d.suffix == ".3dshapes":
                files: list[dict[str, Any]] = []
                for m in sorted(d.iterdir()):
                    if m.is_file() and m.suffix.lower() in (".wrl", ".step", ".stp", ".gz"):
                        name = m.name
                        ext = m.suffix.lower()
                        if name.endswith(".step.gz"):
                            ext = "step.gz"
                        size_kb = round(m.stat().st_size / 1024, 1)
                        files.append({"name": name, "extension": ext, "size_kb": size_kb})
                results.append(
                    ModelEntry(
                        lib_name=d.stem.replace(".3dshapes", ""),
                        dir_path=d,
                        model_files=files,
                    )
                )
        return results

    def scan_all(self) -> dict[str, list[Any]]:
        return {
            "symbols": self.scan_symbols(),
            "footprints": self.scan_footprints(),
            "models": self.scan_models(),
        }

    def get_summary(self) -> dict[str, int]:
        syms = self.scan_symbols()
        fps = self.scan_footprints()
        mods = self.scan_models()
        return {
            "symbol_libs": len(syms),
            "symbol_count": sum(len(s.symbol_names) for s in syms),
            "footprint_libs": len(fps),
            "footprint_count": sum(f.file_count for f in fps),
            "model_libs": len(mods),
            "model_count": sum(len(m.model_files) for m in mods),
        }
