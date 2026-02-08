using System;
using System.Runtime.InteropServices;

namespace Memact.Platform
{
    public static class NativeWin32
    {
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
        [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);

        public struct RECT { public int Left, Top, Right, Bottom; }
        public struct POINT { public int X, Y; }
    }
}
