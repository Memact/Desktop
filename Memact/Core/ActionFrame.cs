using System;
using System.Collections.Generic;
using System.Windows;
using OpenCvSharp;

namespace Memact.Core
{
    public class ActionFrame
    {
        public DateTime Timestamp { get; set; }

        public IntPtr Hwnd { get; set; }

        public Rect Bounds { get; set; }

        public Point Cursor { get; set; }

        public List<Mat> Anchors { get; set; } = new();

        public double Confidence { get; set; } = 0.6;

        public int Attempts { get; set; } = 0;
    }
}
