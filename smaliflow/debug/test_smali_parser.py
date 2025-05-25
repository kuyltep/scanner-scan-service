import enum
import gc
import linecache
import logging
import os
import subprocess
import sys
import threading
import time
import tracemalloc
from types import FrameType

import psutil
import tqdm

from smalivm import Vm
from smalivm.smali.instructions import Instruction, NewInstance
from smalivm.smali.labels import LabelsContext
from smalivm.smali.members import Class, Method
from smalivm.smali.reader import Reader
from smalivm.smali.registers import Register, RegistersContext, RegisterValue
from smalivm.smalivm import InstructionsRunner, MethodRunner


def progress_bar(
    current: int, total: int, start_time: float, bar_length: int = 40
) -> None:
    """
    Отображает прогресс-бар в консоли и подсчитывает время работы.

    :param current: Текущее значение (индекс или итерация)
    :param total: Общее количество итераций
    :param start_time: Время начала работы (в секундах с начала эпохи)
    :param bar_length: Длина прогресс-бара в символах (по умолчанию 40)
    """
    progress = current / total
    block = int(bar_length * progress)
    bar = "=" * block + "-" * (bar_length - block)
    percentage = progress * 100
    elapsed_time = time.time() - start_time
    if 5 <= elapsed_time <= 5:
        print("")
    sys.stdout.write(
        f"\r[{bar}] {percentage:.2f}% ({current}/{total}) Elapsed Time: {elapsed_time:.2f}s"
    )
    sys.stdout.flush()

    if current == total:
        print()


def decompile_apk() -> list[str]:
    in_paths = [
        # "/home/kiber/smaliflow/com.perm.kate_560.apk",
        # "/mnt/c/Users/ogusainov/AndroidStudioProjects/VulnApk/app/build/intermediates/apk/debug/app-debug.apk",
        # "/mnt/c/Users/ogusainov/StudioProjects/XAppDebug/app/release/XAppDebug_1.0.7.apk",
        # "/tmp/stub_smali",
        # "/tmp/stub_smali2",
        # "/home/kiber/smaliflow/com.thetrainline_1241771.apk",
        # "/home/kiber/smaliflow/com.thetransitapp.droid_19222.apk"
        # "/home/kiber/smaliflow/com.tranzmate_561.apk"
        "../com.wuliang.xapkinstaller-4.6.4.1-v162.apk"
    ]
    [print(os.path.abspath(x)) for x in in_paths]

    out_paths = [f"tests/files/{os.path.basename(x)}_decompiled" for x in in_paths]
    for idx, out_path in enumerate(out_paths):
        if not os.path.exists(out_path):
            in_path = in_paths[idx]
            command = (
                f"java -jar ../vulnapk/apkeditor.jar d -i {in_path} -f -o {out_path}"
            )
            subprocess.run(
                command,
                shell=True,
                check=True,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
            )
    # dir_path = "tests/files/test_decompiled/"
    # if os.path.exists(dir_path):
    #     logging.info(f"Directory {dir_path} already exists, skipping decompilation")
    #     return dir_path
    # apk_path = "/home/kiber/vulnapk/com.perm.kate_560.apk"
    # apk_path = "/home/kiber/vulnapk/apks/com.vkontakte.android_27944.apk"
    # apk_path = "/home/kiber/vulnapk/ru.ozon.app.android_2538.apk"
    # apk_path = "/home/kiber/smaliflow/com.thetrainline_1241097.apk"
    # apk_path = "/home/kiber/smaliflow/com.mapquest.android.ace_1479.apk"
    # apk_path = "/mnt/c/Users/ogusainov/StudioProjects/XAppDebug/app/release/XAppDebug_1.0.7.apk"
    # apk_path = "/mnt/c/Users/ogusainov/AndroidStudioProjects/VulnApk/app/build/intermediates/apk/debug/app-debug.apk"
    # apk_path = "/mnt/c/Users/ogusainov/AndroidStudioProjects/VulnApk/app/build/outputs/apk/debug/app-debug.apk"
    # command = f"java -jar tests/files/apkeditor.jar d -i {apk_path} -f -o {dir_path}"
    # subprocess.run(
    #     command,
    #     shell=True,
    #     check=True,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    # )
    return out_paths


def callback(context: RegistersContext, ins: Instruction):
    print(ins)


def on_value_type(
    context: RegistersContext, ins: Instruction, reg: Register, value: str
) -> None:
    pass
    # print("Value: \"{}\" at {}".format(value, ins))


def display_top(snapshot, key_type="lineno", limit=3):
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        )
    )
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print(
            "#%s: %s:%s: %.1f KiB" % (index, filename, frame.lineno, stat.size / 1024)
        )
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print("    %s" % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))


def gctest() -> None:
    # gc.collect()  # Очистка памяти перед анализом
    objects = gc.get_objects()  # Получаем текущие объекты

    tracked_ids = {
        id(obj) for obj in objects
    }  # Запоминаем ID объектов до создания новых ссылок

    for obj in objects:
        if not isinstance(obj, MethodRunner):
            continue

        refs = []
        for ref in gc.get_referrers(obj):
            if (
                id(ref)
                not in tracked_ids  # Исключаем объекты, созданные внутри этой функции
                or isinstance(ref, FrameType)  # Исключаем стековые фреймы
                or ref is globals()  # Исключаем глобальные переменные
            ):
                continue
            refs.append(ref)

        if refs:
            print(f"Объект:\n    {obj} ({id(obj)})\nСсылающиеся на него:")
            for ref in refs:
                print(f"    - [{type(ref)}] {ref} ({id(ref)})")

    # path = "tests/files/test_classes"


file_count = 0
class_count = 0
method_count = 0

stop_memcount = False


def memcount(bar: tqdm.tqdm) -> None:
    while True:
        if stop_memcount:
            return
        mem = f"{psutil.Process(pid).memory_info().rss / 1024 ** 2:.2f} MB"
        bar.set_description(
            f"Memory usage: {mem} (pid: {pid}) [f {file_count}, c {class_count}, m {method_count}]"
        )
        time.sleep(0.5)


paths = decompile_apk()
for i in range(len(paths)):
    file_count = i
    # gctest()
    path = paths[i]
    print("Creating VM for path:", path)
    vm = Vm(path)
    print("VM created")
    # vm.add_breakpoint_by_custom_condition(lambda x, y: True, callback)
    vm.add_breakpoint_by_value_type("string", on_value_type)
    # vm.invoke_method(
    #     "<clinit>",
    #     [],
    #     "Lpt/kiber/vulnapk/Tokens;",
    # )
    # count = vm.class_count()
    # idx = 0
    # tracemalloc.start()
    # start_time = time.time()
    bar = tqdm.tqdm(
        unit="B",
        unit_scale=True,
        bar_format="{l_bar}{bar}{r_bar}",
        total=vm.class_count(),
    )
    pid = os.getpid()
    thread = threading.Thread(target=memcount, args=(bar,))
    thread.start()

    # snapshot_before = tracemalloc.take_snapshot()
    for idx, cls in enumerate(vm.iter_classes()):
        idx += 1
        class_count = idx
        bar.update()
        # if idx == 310:
        #     pass
        #     def print_top_lines():
        #         while True:
        #             time.sleep(1)
        #             snapshot = tracemalloc.take_snapshot()
        #             display_top(snapshot, limit=5)

        #     thread = threading.Thread(target=print_top_lines, daemon=True)
        #     thread.start()
        # if idx >= 20000:
        # import psutil, os
        # print(f"Memory usage: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2:.2f} MB")
        # gc.collect()
        # print(
        #     f"Memory usage (after GC): {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2:.2f} MB"
        # )
        # if idx == 2000:
        #     gc.collect()
        #     objects = gc.get_objects()
        #     biggest_lists = sorted(
        #         # (obj for obj in objects if isinstance(obj, list)),
        #         objects,
        #         key=sys.getsizeof,
        #         reverse=True,
        #     )
        #     print("\nТОП 5 самых больших списков в памяти:")
        #     for lst in biggest_lists[:5]:
        #         print(
        #             f"Размер: {sys.getsizeof(lst) / 1024 / 1024:.2f} MB, Объект: {lst}"
        #         )

        # Группируем объекты по типу
        # size_by_type = Counter()
        # for obj in objects:
        #     try:
        #         size_by_type[type(obj)] += sys.getsizeof(obj)
        #     except:
        #         pass  # Пропускаем ошибки

        # print("\nТОП 10 типов объектов по потреблению памяти:")
        # for obj_type, size in size_by_type.most_common(10):
        #     print(f"{obj_type}: {size / 1024 / 1024:.2f} MB")

        # snapshot_after = tracemalloc.take_snapshot()
        # stats = snapshot_after.compare_to(snapshot_before, "lineno")
        # for stat in stats[:5]:
        #     print(stat)
        # print(display_top(snapshot, limit=10))
        # exit(1)
        # while True:
        #     time.sleep(10)
        # progress_bar(idx, count, start_time)
        if cls.is_framework():
            continue
        vm.run_all_methods(cls)
        #     bar.set_description(f"Memory usage: {mem} (pid: {pid}) [#{i}] [#{midx}]")
        # cls_ref = weakref.ref(cls)
        # for ref in gc.get_referrers(cls):
        #     print("    - " + str(ref) + f"({id(ref)})")
        # del cls
        # gc.collect()
        # if cls_ref() is not None:
        #     for ref in gc.get_referrers(cls_ref()):
        #         print("    - " + str(ref) + f"({id(ref)})")
        #     print(f"Memory leak detected for class {cls_ref}")
        #     exit(1)
        # gc.collect()
    # gc.collect()
    # del vm
    # leaked_objects = [
    #     obj for obj in gc.get_objects() if isinstance(obj, Class)
    # ]
    # gc.collect()
    # t = threading.Thread(target=time.sleep, args=(10,))
    # t.start()
    # t.join()
    # objects = gc.get_objects()
    # for obj in objects:
    #     if not isinstance(obj, Method):
    #         continue
    #     refs = [ref for ref in gc.get_referrers(obj) if ref != objects and ref != globals()]
    #     if refs:
    #         print(f"Объект:\n    {obj} ({id(obj)})\nСсылающиеся на него:")
    #     for ref in refs:
    #         # if isinstance(ref, list):
    #         #     for i in ref:
    #         #         print("    - " + str(i) + f"({id(i)})")
    #         # else:
    #         print("    - " +  f"[{type(ref)}]" + str(ref) + f"({id(ref)})")
    # print(sys.getrefcount(cls), cls.is_framework())
    stop_memcount = True


#! LDelayRepayUKAddBankDetailsMainBodyContentKt$DelayRepayAddBankDetailsMainBodyContent$2;->a(Landroidx/compose/runtime/Composer;I)V
