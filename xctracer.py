import argparse
import subprocess
import os
import glob


class Builder:
    @staticmethod
    def find_project_workspace(directory):
        print("正在当前目录查找.xcworkspace或.xcodeproj...")
        workspace_files = glob.glob(os.path.join(directory, "*.xcworkspace"))
        project_files = glob.glob(os.path.join(directory, "*.xcodeproj"))
        if workspace_files or project_files:
            print("已找到项目/工作空间文件。")
        else:
            print("未找到项目/工作空间文件。")
        return (
            workspace_files[0] if workspace_files else None,
            project_files[0] if project_files else None,
        )

    @staticmethod
    def compile_app(args):
        directory = os.getcwd()
        print("开始构建过程...")

        if not args.xcworkspace and not args.xcodeproj:
            print("未提供工作空间或项目路径。尝试自动查找...")
            args.xcworkspace, args.xcodeproj = Builder.find_project_workspace(directory)

        project_type = "-workspace" if args.xcworkspace else "-project"
        project_path = args.xcworkspace or args.xcodeproj

        if not project_path:
            raise ValueError("在当前目录未找到.xcworkspace或.xcodeproj文件。")

        print(f"使用{'工作空间' if project_type == '-workspace' else '项目'}: {project_path}")

        sdk = "iphoneos" if args.device == "real" else "iphonesimulator"
        print(
            f"为{'真机' if sdk == 'iphoneos' else '模拟器'}构建 ({args.arch}) 配置为 {args.configuration}"
        )

        if not args.scheme:
            if args.xcworkspace:
                scheme_name = os.path.splitext(os.path.basename(args.xcworkspace))[0]
            elif args.xcodeproj:
                scheme_name = os.path.splitext(os.path.basename(args.xcodeproj))[0]
            else:
                raise ValueError("未提供scheme且未发现.xcworkspace或.xcodeproj文件。")
            args.scheme = scheme_name

        build_command_common = [
            "xcodebuild",
            project_type,
            project_path,
            "-scheme",
            args.scheme,
            "-configuration",
            args.configuration,
            "-sdk",
            sdk,
            "-arch",
            args.arch,
            "clean",
            "build",
        ]

        output_dir = os.path.join(directory, "Archive")
        if not os.path.exists(output_dir):
            print("创建构建输出目录...")
            os.makedirs(output_dir)

        build_command = build_command_common + ["-derivedDataPath", output_dir]
        print(f"执行构建命令:{build_command}")
        #    {' '.join(build_command)}")

        subprocess.run(build_command, check=True)

        product_dir = (
            "Release-iphoneos"
            if sdk == "iphoneos"
            else f"{args.configuration}-iphonesimulator"
        )
        app_path = os.path.join(
            output_dir, "Build/Products", product_dir, args.scheme + ".app"
        )
        if os.path.exists(app_path):
            print(f"构建成功。应用位置：{app_path}")
        else:
            print("构建失败。未找到应用路径。")
        return app_path


class XCTrace:
    @staticmethod
    def record(args, app_path):
        # Use xctrace to record performance data
        pass

    @staticmethod
    def export_trace(trace_path):
        # Export the recorded trace data to an XML file
        pass


class BuildArgs:
    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            "--xcworkspace", type=str, help="Path to the .xcworkspace file"
        )
        parser.add_argument("--xcodeproj", type=str, help="Path to the .xcodeproj file")
        parser.add_argument("--scheme", type=str, help="The build scheme")
        parser.add_argument(
            "--configuration", default="Debug", type=str, help="Build configuration"
        )
        parser.add_argument(
            "--arch", default="x86_64", type=str, help="Architecture to build for"
        )
        parser.add_argument(
            "--device",
            default="simulator",
            choices=["simulator", "real"],
            help="Target device: simulator (default) or real device",
        )
        build_args, _ = parser.parse_known_args()
        return build_args


class XCTraceArgs:
    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            "--app",
            "-a",
            help="The path to the .app file. If provided, compilation is skipped.",
        )
        parser.add_argument(
            "--template",
            "-t",
            default="Leaks",
            help="The instrument template name to use for recording (e.g., Leaks, Time Profiler). Default is Leaks.",
        )
        parser.add_argument(
            "--output",
            "-o",
            default="output.trace",
            help="The output path for the .trace file.",
        )
        trace_args, _ = parser.parse_known_args()
        return trace_args


class Pipeline:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="XCTracer: A helper script for building and tracing iOS apps."
        )
        self.parser.add_argument(
            "--mode",
            choices=["build", "trace", "all"],
            default="all",
            help="Mode to run the script in: build, trace, or all (default).",
        )
        self.build_args = BuildArgs.parse_arguments()
        self.xctrace_args = XCTraceArgs.parse_arguments()
        self.args = self.parser.parse_args()

    def run(self):
        if self.args.mode in ["build", "all"]:
            # 如果模式是 build 或 all, 运行构建过程
            if not self.xctrace_args.app:
                Builder.compile_app(self.build_args)

        if self.args.mode in ["trace", "all"]:
            # 如果模式是 trace 或 all, 运行跟踪过程
            app_path = (
                self.xctrace_args.app
                if self.xctrace_args.app
                else self.build_args.scheme + ".app"
            )
            # Now, record the trace
            trace_path = XCTrace.record(self.xctrace_args, app_path)
            # Finally, export the trace to XML
            XCTrace.export_trace(trace_path)


if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.run()
