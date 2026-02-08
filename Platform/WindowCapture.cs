using System;
using System.Drawing;
using System.Windows;
using Memact.Core;
using OpenCvSharp;
using OpenCvSharp.Extensions;

namespace Memact.Platform
{
    public static class WindowCapture
    {
        public static ActionFrame? Capture()
        {
            try
            {
                var hwnd = NativeWin32.GetForegroundWindow();
                NativeWin32.GetWindowRect(hwnd, out var r);
                NativeWin32.GetCursorPos(out var p);

                int w = r.Right - r.Left;
                int h = r.Bottom - r.Top;
                if (w <= 0 || h <= 0) return null;

                using var bmp = new Bitmap(w, h);
                using (var g = Graphics.FromImage(bmp))
                    g.CopyFromScreen(r.Left, r.Top, 0, 0, bmp.Size);

                var mat = BitmapConverter.ToMat(bmp);

                int cx = Math.Clamp(p.X - r.Left, 0, w - 1);
                int cy = Math.Clamp(p.Y - r.Top, 0, h - 1);

                int ax = Math.Max(0, cx - 32);
                int ay = Math.Max(0, cy - 32);

                var anchor = mat.SubMat(new Rect(ax, ay,
                    Math.Min(64, w - ax),
                    Math.Min(64, h - ay)));

                return new ActionFrame
                {
                    Timestamp = DateTime.Now,
                    Hwnd = hwnd,
                    Bounds = new Rect(r.Left, r.Top, w, h),
                    Cursor = new Point(cx, cy),
                    Anchors = { anchor }
                };
            }
            catch { return null; }
        }
    }
}
