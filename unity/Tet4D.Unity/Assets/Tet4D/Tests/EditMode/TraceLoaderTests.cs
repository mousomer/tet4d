using NUnit.Framework;
using Tet4D.UnityReplay.TraceReplay;

namespace Tet4D.UnityReplay.Tests
{
    public sealed class TraceLoaderTests
    {
        [Test]
        public void SampleTraceCasesLoadForEachFamily()
        {
            TraceBundle bundle = TraceLoader.LoadBundle(TraceTestPaths.BundleRoot());

            TraceDocument topology = TraceLoader.LoadCaseDocument(
                bundle,
                bundle.CasesForTraceType("topology")[0]
            );
            TraceDocument gameplay = TraceLoader.LoadCaseDocument(
                bundle,
                bundle.CasesForTraceType("gameplay")[0]
            );
            TraceDocument endgame = TraceLoader.LoadCaseDocument(
                bundle,
                bundle.CasesForTraceType("endgame")[0]
            );

            Assert.That(topology.Frames.Count, Is.GreaterThan(0));
            Assert.That(gameplay.Frames.Count, Is.GreaterThan(0));
            Assert.That(endgame.Frames.Count, Is.GreaterThan(0));
            Assert.That(topology.CaseId, Is.Not.Empty);
            Assert.That(gameplay.CaseId, Is.Not.Empty);
            Assert.That(endgame.CaseId, Is.Not.Empty);
        }
    }
}
