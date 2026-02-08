using System.Linq;
using Memact.Core;
using OpenCvSharp;

namespace Memact.Vision
{
    public static class TemplateMatcher
    {
        public static (bool ok, OpenCvSharp.Point pos, double score) Match(Mat current, ActionFrame frame)
        {
            double best = 0;
            OpenCvSharp.Point bestLoc = default;

            foreach (var a in frame.Anchors)
            {
                using var res = new Mat();
                Cv2.MatchTemplate(current, a, res, TemplateMatchModes.CCoeffNormed);
                Cv2.MinMaxLoc(res, out _, out double max, out _, out OpenCvSharp.Point loc);

                if (max > best)
                {
                    best = max;
                    bestLoc = loc;
                }
            }

            return (best >= 0.75, bestLoc, best);
        }
    }
}
