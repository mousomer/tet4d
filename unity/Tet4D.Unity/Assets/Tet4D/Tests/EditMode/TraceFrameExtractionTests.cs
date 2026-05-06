using NUnit.Framework;
using Tet4D.UnityReplay.TraceReplay;

namespace Tet4D.UnityReplay.Tests
{
    public sealed class TraceFrameExtractionTests
    {
        [Test]
        public void GameplaySnapshotExtractsActiveAndLockedCells()
        {
            TraceBundle bundle = TraceLoader.LoadBundle(TraceTestPaths.BundleRoot());
            TraceDocument document = TraceLoader.LoadCaseDocument(
                bundle,
                bundle.CasesForTraceType("gameplay")[0]
            );

            TraceRenderSnapshot snapshot = TraceSnapshotExtractor.Extract(document, 0);

            Assert.That(snapshot.ActiveCells.Count, Is.GreaterThanOrEqualTo(0));
            Assert.That(snapshot.StateHash, Is.Not.Empty);
            Assert.That(snapshot.MetadataText, Does.Contain("Gameplay Replay"));
        }

        [Test]
        public void TopologySnapshotExtractsProbeMarkers()
        {
            TraceBundle bundle = TraceLoader.LoadBundle(TraceTestPaths.BundleRoot());
            TraceDocument document = TraceLoader.LoadCaseDocument(
                bundle,
                bundle.CasesForTraceType("topology")[0]
            );

            TraceRenderSnapshot snapshot = TraceSnapshotExtractor.Extract(document, 0);

            Assert.That(snapshot.ProbeMarkers.Count, Is.GreaterThan(0));
            Assert.That(snapshot.StateHash, Is.Not.Empty);
        }

        [Test]
        public void EndgameSnapshotExtractsParticles()
        {
            TraceBundle bundle = TraceLoader.LoadBundle(TraceTestPaths.BundleRoot());
            TraceDocument document = TraceLoader.LoadCaseDocument(
                bundle,
                bundle.CasesForTraceType("endgame")[0]
            );

            TraceRenderSnapshot snapshot = TraceSnapshotExtractor.Extract(document, 0);

            Assert.That(snapshot.Particles.Count, Is.GreaterThan(0));
            Assert.That(snapshot.MetadataText, Does.Contain("Endgame Replay"));
        }
    }
}
