using System;
using System.Drawing;
using System.Threading.Tasks;
using System.Windows;
using Memact.Core;
using Memact.Hooks;
using Memact.Platform;
using Memact.UI;
using Memact.Vision;
using OpenCvSharp.Extensions;

namespace Memact
{
    public class Program : Application
    {
        private static FrameBuffer Buffer = new();
        private static TriggerGate Gate = new();
        private static CapsRecall Caps = new();

        [STAThread]
        public static void Main()
        {
            GlobalHooks.Install();

            // Algorithm 0
            GlobalHooks.MouseUp += () => Gate.OnMouseUp();

            // Algorithm 1
            Gate.Trigger += () =>
            {
                var frame = WindowCapture.Capture();
                if (frame != null)
                    Buffer.Add(frame);
            };

            // Caps Recall
            GlobalHooks.CapsDown += () => Caps.Down();
            GlobalHooks.CapsUp += () => Caps.Up();

            // Algorithm 2 + 3 + 4
            Caps.Recall += async () =>
            {
                if (Buffer.Empty) return;

                foreach (var f in Buffer.All())
                    if (ConfidenceEngine.ShouldPrune(f))
                        Buffer.Remove(f);

                var frame = Buffer.Best();
                if (frame == null) return;

                var currentFrame = WindowCapture.Capture();
                if (currentFrame == null) return;

                var mat = currentFrame.Anchors[0];

                var (ok, pos, score) = TemplateMatcher.Match(mat, frame);

                ConfidenceEngine.Update(frame, ok);

                if (!ok) return; // silent failure

                var overlay = new Overlay
                {
                    Left = frame.Bounds.Left + pos.X,
                    Top = frame.Bounds.Top + pos.Y
                };

                overlay.Show();
                await Task.Delay(2000);
                overlay.Close();
            };

            new Program().Run();
        }
    }
}
