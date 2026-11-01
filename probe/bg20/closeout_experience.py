# -*- coding: utf-8 -*-
"""bg20 收尾：回流到 mod_experience（附录 D 一行 + ex/04 规则 117），并自证「删除 0 行」。

判据：两个文件的新文本 **删掉插入块后必须与旧文本逐字节相同** ⇒ 旧内容一行没动。
"""
import hashlib
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\mc\mcmod\mod_experience"

ROW = (
    "| 2026-11-01 | bettergold | **`bg20`（P4）：手册「混沌金的主要内容」重做 + 自定义页型 "
    "`bettergold:double_recipe`** | **指针**：Patchouli 1.21.1-93 的页面 API 事实（**没有** `Page` / "
    "`Codec` / `StreamCodec` / `registerPageType`；注册入口 = `ClientBookRegistry.INSTANCE.pageTypes` 这张 "
    "public 表；`type` 查不到**静默回落** `PageTemplate`）与「protected 画法靠子类借画笔」手法，见 "
    "`ex\\04-数值与API.md` **规则 117**；本项目侧全文见 `bettergold\\docs\\1.7-混沌金与崩乱合金-需求立档.md` §33 | "
    "未写：**14 件 / 7 页 / 上粒下锭**这类本项目页数口径只对本项目成立（已写项目 docs §33.3）；"
    "A 级读数 `bettergold\\docs\\bg20-证据\\10-客户端-BookContents.txt`（20 PASS / 0 FAIL） |"
)

RULE = """
### 规则 117（2026-11-01，bettergold bg20 轮）：给 Patchouli 加**自定义页型** —— 本版本没有 Codec/StreamCodec，注册入口是一张 **public** 的 `pageTypes` 表

- **现象**：要给书加一个「一页上 / 下各一条配方、两条还可以是不同 recipe class」的页；按新版教程去找
  `Page` / `Codec` / `StreamCodec` / `PageTypeRegistry` / `registerPageType` —— **全都不存在**。
- **根因（`javap -p -c` 反编译 `Patchouli-1.21.1-93-NEOFORGE.jar`，无 sources）**：
  1. 页面基类 = `vazkii.patchouli.client.book.BookPage`：字段 `type` / `sourceObject`（public，原始 json）+
     一堆 `public transient`（`parent` / `book` / `left` / `top`，**`onDisplayed(...)` 才填**）；
     反序列化 = `ClientBookRegistry$LexiconPageAdapter`（GSON）：读 `type` → 无冒号补 `patchouli:` →
     查 `pageTypes` → `SerializationUtil.RAW_GSON.fromJson`。**查不到不报错**，静默回落 `PageTemplate`
     ⇒ 页型名写错只能靠静态关卡 + A 级探针抓（不能指望日志）。
  2. 注册入口 = **`ClientBookRegistry.INSTANCE.pageTypes`（public `Map<ResourceLocation, Class<? extends BookPage>>`）**；
     `addPageTypes()` 只 `put`、**从不清空** ⇒ 与 Patchouli 自己 `init()` 的先后顺序无关。
     `api/PatchouliAPI$IPatchouliAPI` 里**没有** `registerPageType`。
  3. 书内容在**客户端** `assets/<ns>/patchouli_books/…` ⇒ **没有"网络同步"这一关**（页面不跨端传）。
  4. `PageDoubleRecipe#render` 本身就是「上 / 下两格」（recipe2 在 `y + getRecipeHeight() − (title2 空?10:0)`）
     ⇒ 自定义页**不必自己排版**，只要按 **recipe 的实际类**分派画法；`getRecipeHeight()` 决定两格间距。
  5. `PageCrafting#drawRecipe` / `PageSimpleProcessingRecipe#drawRecipe` 都是 `protected` ⇒ **跨包调不到**。
     **手法**：写两个 `private static` 子类（`extends PageCrafting` / `extends PageSmelting`），在**子类内部**
     调自己的继承方法，再把宿主页的 `book` / `parent` / `mc` / `fontRenderer` **搬**过去；
     ⚠ `title1` / `title2` 也是 `protected` 且跨包只能经**本类类型**的引用访问 ⇒ **标题必须传参**进去，
     不能从宿主对象上读。
- **规则**：给 Patchouli 加页型前先 `javap` 确认**这个版本的**基类与注册表（大版本之间 API 完全不同）；
  落法是「**注册表 put + 子类借画笔**」。在**可选依赖口径 B（没装就不注册）**下，页面类在**类声明**上就会解析
  对方的类型 ⇒ 它只许在 `isLoaded()` 守卫**之后**被 `.class` 触碰，并单独列进"引用 Patchouli 的文件"白名单
  （白名单从 1 个文件扩成 2 个，关卡的期望同步改，且要断言"恰好这两个"）。
- **依据等级**：`javap -p -c` 逐类反汇编【读源码】+【A 级】客户端真加载 `BookContents`：
  `pageTypes[bettergold:double_recipe]` 命中、第 4 章 10 页、自定义页上下两条分别是 `SmeltingRecipe`
  与 `ShapedRecipe`、`errored=false`、全书 227 条配方引用 0 死链（**20 PASS / 0 FAIL**）。
- **位置**：`bettergold/docs/1.7-混沌金与崩乱合金-需求立档.md` §33（§33.1 = 事实表）；
  A 级读数 `bettergold/docs/bg20-证据/10-客户端-BookContents.txt`。
"""


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def main():
    ok = True
    # ---- ① 附录 D：在表格**最后一行之后**插入一行（不动旧行） ----
    p1 = ROOT + r"\mcmod_experience.md"
    old1 = io.open(p1, encoding="utf-8", newline="").read()
    lines = old1.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## 附录 D"))
    nxt = [i for i, l in enumerate(lines) if l.startswith("## ") and i > start]
    end = nxt[0] if nxt else len(lines)
    rows = [i for i in range(start, end) if lines[i].startswith("|")]
    last = rows[-1]
    if "bg19" not in lines[last]:
        print("!! 附录 D 最后一行不是 bg19（旧行定位可疑）：", lines[last][:80])
        ok = False
    insert_row = ROW + "\n"
    new1 = "\n".join(lines[:last + 1]) + "\n" + insert_row + "\n".join(lines[last + 1:])
    io.open(p1, "w", encoding="utf-8", newline="").write(new1)
    check1 = new1.replace(insert_row, "", 1) == old1
    print("附录 D: 插在第 %d 行之后 / 删掉插入行后与旧文本逐字节相同 = %s" % (last + 1, check1))
    print("   SHA256 %s -> %s" % (sha_old(p1, old1), sha(p1)))
    ok = ok and check1

    # ---- ② ex/04：追加规则 117（纯追加） ----
    p2 = ROOT + r"\ex\04-数值与API.md"
    old2 = io.open(p2, encoding="utf-8", newline="").read()
    add = ("" if old2.endswith("\n") else "\n") + RULE
    io.open(p2, "w", encoding="utf-8", newline="").write(old2 + add)
    new2 = io.open(p2, encoding="utf-8", newline="").read()
    check2 = new2.endswith(RULE) and new2.startswith(old2)
    print("ex/04: 追加 规则 117 / 旧文本是不是新文本的前缀 = %s（旧 %d 行 -> 新 %d 行）"
          % (check2, old2.count("\n"), new2.count("\n")))
    print("   SHA256 %s -> %s" % (sha_old(p2, old2), sha(p2)))
    ok = ok and check2

    print("结论:", "两个文件都只增不改（删除 0 行）" if ok else "!! 有异常")
    return 0 if ok else 1


def sha_old(path, text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


if __name__ == "__main__":
    sys.exit(main())
