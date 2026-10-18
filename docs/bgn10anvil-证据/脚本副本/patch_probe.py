import sys
sys.stdout.reconfigure(errors="replace")
p = r"E:\mc\mcmod\bettergold-template-1.21.1\probe\bgn10anvil\BgN10anvilServerProbe.java"
s = open(p, "rb").read().decode("utf-8")
old = '''        dummy.connection = new ServerGamePacketListenerImpl(server,
                new Connection(PacketFlow.SERVERBOUND), dummy,
                CommonListenerCookie.createInitial(new GameProfile(UUID.randomUUID(), "bgn10anvilprobe"), false));'''
new = '''        Connection conn = new Connection(PacketFlow.SERVERBOUND);
        try {
            // Neoforge 的 hasChannel() 会直接 channel().attr(...) ⇒ 没有 channel 会 NPE（轮8 同一个坑）
            java.lang.reflect.Field chf = Connection.class.getDeclaredField("channel");
            chf.setAccessible(true);
            chf.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
        } catch (Throwable t) {
            bettergold.LOGGER.error("{} channel setup failed", TAG, t);
        }
        dummy.connection = new ServerGamePacketListenerImpl(server, conn, dummy,
                CommonListenerCookie.createInitial(new GameProfile(UUID.randomUUID(), "bgn10anvilprobe"), false));'''
assert s.count(old) == 1, "anchor"
s = s.replace(old, new)
open(p, "wb").write(s.encode("utf-8"))
print("patched")
