package net.minecraft.server;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonIOException;
import com.google.gson.JsonParseException;
import com.google.gson.internal.Streams;
import com.google.gson.stream.JsonReader;
import com.mojang.datafixers.DataFixer;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import java.io.IOException;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;
import java.util.function.BiConsumer;
import javax.annotation.Nullable;
import net.minecraft.FileUtil;
import net.minecraft.advancements.Advancement;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementNode;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.advancements.AdvancementTree;
import net.minecraft.advancements.Criterion;
import net.minecraft.advancements.CriterionProgress;
import net.minecraft.advancements.CriterionTrigger;
import net.minecraft.advancements.CriterionTriggerInstance;
import net.minecraft.advancements.DisplayInfo;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.protocol.game.ClientboundSelectAdvancementsTabPacket;
import net.minecraft.network.protocol.game.ClientboundUpdateAdvancementsPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.advancements.AdvancementVisibilityEvaluator;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.GameRules;
import org.slf4j.Logger;

public class PlayerAdvancements {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private final PlayerList playerList;
    private final Path playerSavePath;
    private AdvancementTree tree;
    private final Map<AdvancementHolder, AdvancementProgress> progress = new LinkedHashMap<>();
    private final Set<AdvancementHolder> visible = new HashSet<>();
    private final Set<AdvancementHolder> progressChanged = new HashSet<>();
    private final Set<AdvancementNode> rootsToUpdate = new HashSet<>();
    private ServerPlayer player;
    @Nullable
    private AdvancementHolder lastSelectedTab;
    private boolean isFirstPacket = true;
    private final Codec<PlayerAdvancements.Data> codec;

    public PlayerAdvancements(DataFixer dataFixer, PlayerList playerList, ServerAdvancementManager manager, Path playerSavePath, ServerPlayer player) {
        this.playerList = playerList;
        this.playerSavePath = playerSavePath;
        this.player = player;
        this.tree = manager.tree();
        int i = 1343;
        this.codec = DataFixTypes.ADVANCEMENTS.wrapCodec(PlayerAdvancements.Data.CODEC, dataFixer, 1343);
        this.load(manager);
    }

    public void setPlayer(ServerPlayer player) {
        this.player = player;
    }

    public void stopListening() {
        for (CriterionTrigger<?> criteriontrigger : BuiltInRegistries.TRIGGER_TYPES) {
            criteriontrigger.removePlayerListeners(this);
        }
    }

    public void reload(ServerAdvancementManager manager) {
        this.stopListening();
        this.progress.clear();
        this.visible.clear();
        this.rootsToUpdate.clear();
        this.progressChanged.clear();
        this.isFirstPacket = true;
        this.lastSelectedTab = null;
        this.tree = manager.tree();
        this.load(manager);
    }

    private void registerListeners(ServerAdvancementManager manager) {
        for (AdvancementHolder advancementholder : manager.getAllAdvancements()) {
            this.registerListeners(advancementholder);
        }
    }

    private void checkForAutomaticTriggers(ServerAdvancementManager manager) {
        for (AdvancementHolder advancementholder : manager.getAllAdvancements()) {
            Advancement advancement = advancementholder.value();
            if (advancement.criteria().isEmpty()) {
                this.award(advancementholder, "");
                advancement.rewards().grant(this.player);
            }
        }
    }

    private void load(ServerAdvancementManager manager) {
        if (Files.isRegularFile(this.playerSavePath)) {
            try (JsonReader jsonreader = new JsonReader(Files.newBufferedReader(this.playerSavePath, StandardCharsets.UTF_8))) {
                jsonreader.setLenient(false);
                JsonElement jsonelement = Streams.parse(jsonreader);
                PlayerAdvancements.Data playeradvancements$data = this.codec.parse(JsonOps.INSTANCE, jsonelement).getOrThrow(JsonParseException::new);
                this.applyFrom(manager, playeradvancements$data);
            } catch (JsonIOException | IOException ioexception) {
                LOGGER.error("Couldn't access player advancements in {}", this.playerSavePath, ioexception);
            } catch (JsonParseException jsonparseexception) {
                LOGGER.error("Couldn't parse player advancements in {}", this.playerSavePath, jsonparseexception);
            }
        }

        this.checkForAutomaticTriggers(manager);
        this.registerListeners(manager);
    }

    public void save() {
        JsonElement jsonelement = this.codec.encodeStart(JsonOps.INSTANCE, this.asData()).getOrThrow();

        try {
            FileUtil.createDirectoriesSafe(this.playerSavePath.getParent());

            try (Writer writer = Files.newBufferedWriter(this.playerSavePath, StandardCharsets.UTF_8)) {
                GSON.toJson(jsonelement, GSON.newJsonWriter(writer));
            }
        } catch (JsonIOException | IOException ioexception) {
            LOGGER.error("Couldn't save player advancements to {}", this.playerSavePath, ioexception);
        }
    }

    private void applyFrom(ServerAdvancementManager advancementManager, PlayerAdvancements.Data data) {
        data.forEach((p_300732_, p_300733_) -> {
            AdvancementHolder advancementholder = advancementManager.get(p_300732_);
            if (advancementholder == null) {
                LOGGER.warn("Ignored advancement '{}' in progress file {} - it doesn't exist anymore?", p_300732_, this.playerSavePath);
            } else {
                this.startProgress(advancementholder, p_300733_);
                this.progressChanged.add(advancementholder);
                this.markForVisibilityUpdate(advancementholder);
            }
        });
    }

    private PlayerAdvancements.Data asData() {
        Map<ResourceLocation, AdvancementProgress> map = new LinkedHashMap<>();
        this.progress.forEach((p_300724_, p_300725_) -> {
            if (p_300725_.hasProgress()) {
                map.put(p_300724_.id(), p_300725_);
            }
        });
        return new PlayerAdvancements.Data(map);
    }

    public boolean award(AdvancementHolder advancement, String criterionKey) {
        // Forge: don't grant advancements for fake players
        if (this.player instanceof net.neoforged.neoforge.common.util.FakePlayer) return false;
        boolean flag = false;
        AdvancementProgress advancementprogress = this.getOrStartProgress(advancement);
        boolean flag1 = advancementprogress.isDone();
        if (advancementprogress.grantProgress(criterionKey)) {
            this.unregisterListeners(advancement);
            this.progressChanged.add(advancement);
            flag = true;
            net.neoforged.neoforge.event.EventHooks.onAdvancementProgressedEvent(this.player, advancement, advancementprogress, criterionKey, net.neoforged.neoforge.event.entity.player.AdvancementEvent.AdvancementProgressEvent.ProgressType.GRANT);
            if (!flag1 && advancementprogress.isDone()) {
                advancement.value().rewards().grant(this.player);
                advancement.value().display().ifPresent(p_352686_ -> {
                    if (p_352686_.shouldAnnounceChat() && this.player.level().getGameRules().getBoolean(GameRules.RULE_ANNOUNCE_ADVANCEMENTS)) {
                        this.playerList.broadcastSystemMessage(p_352686_.getType().createAnnouncement(advancement, this.player), false);
                    }
                    net.neoforged.neoforge.event.EventHooks.onAdvancementEarnedEvent(this.player, advancement);
                });
            }
        }

        if (!flag1 && advancementprogress.isDone()) {
            this.markForVisibilityUpdate(advancement);
        }

        return flag;
    }

    public boolean revoke(AdvancementHolder advancement, String criterionKey) {
        boolean flag = false;
        AdvancementProgress advancementprogress = this.getOrStartProgress(advancement);
        boolean flag1 = advancementprogress.isDone();
        if (advancementprogress.revokeProgress(criterionKey)) {
            this.registerListeners(advancement);
            this.progressChanged.add(advancement);
            flag = true;
            net.neoforged.neoforge.event.EventHooks.onAdvancementProgressedEvent(this.player, advancement, advancementprogress, criterionKey, net.neoforged.neoforge.event.entity.player.AdvancementEvent.AdvancementProgressEvent.ProgressType.REVOKE);
        }

        if (flag1 && !advancementprogress.isDone()) {
            this.markForVisibilityUpdate(advancement);
        }

        return flag;
    }

    private void markForVisibilityUpdate(AdvancementHolder advancement) {
        AdvancementNode advancementnode = this.tree.get(advancement);
        if (advancementnode != null) {
            this.rootsToUpdate.add(advancementnode.root());
        }
    }

    private void registerListeners(AdvancementHolder advancement) {
        AdvancementProgress advancementprogress = this.getOrStartProgress(advancement);
        if (!advancementprogress.isDone()) {
            for (Entry<String, Criterion<?>> entry : advancement.value().criteria().entrySet()) {
                CriterionProgress criterionprogress = advancementprogress.getCriterion(entry.getKey());
                if (criterionprogress != null && !criterionprogress.isDone()) {
                    this.registerListener(advancement, entry.getKey(), entry.getValue());
                }
            }
        }
    }

    private <T extends CriterionTriggerInstance> void registerListener(AdvancementHolder advancement, String criterionKey, Criterion<T> criterion) {
        criterion.trigger().addPlayerListener(this, new CriterionTrigger.Listener<>(criterion.triggerInstance(), advancement, criterionKey));
    }

    private void unregisterListeners(AdvancementHolder advancement) {
        AdvancementProgress advancementprogress = this.getOrStartProgress(advancement);

        for (Entry<String, Criterion<?>> entry : advancement.value().criteria().entrySet()) {
            CriterionProgress criterionprogress = advancementprogress.getCriterion(entry.getKey());
            if (criterionprogress != null && (criterionprogress.isDone() || advancementprogress.isDone())) {
                this.removeListener(advancement, entry.getKey(), entry.getValue());
            }
        }
    }

    private <T extends CriterionTriggerInstance> void removeListener(AdvancementHolder advancement, String criterionKey, Criterion<T> criterion) {
        criterion.trigger().removePlayerListener(this, new CriterionTrigger.Listener<>(criterion.triggerInstance(), advancement, criterionKey));
    }

    public void flushDirty(ServerPlayer serverPlayer) {
        if (this.isFirstPacket || !this.rootsToUpdate.isEmpty() || !this.progressChanged.isEmpty()) {
            Map<ResourceLocation, AdvancementProgress> map = new HashMap<>();
            Set<AdvancementHolder> set = new HashSet<>();
            Set<ResourceLocation> set1 = new HashSet<>();

            for (AdvancementNode advancementnode : this.rootsToUpdate) {
                this.updateTreeVisibility(advancementnode, set, set1);
            }

            this.rootsToUpdate.clear();

            for (AdvancementHolder advancementholder : this.progressChanged) {
                if (this.visible.contains(advancementholder)) {
                    map.put(advancementholder.id(), this.progress.get(advancementholder));
                }
            }

            this.progressChanged.clear();
            if (!map.isEmpty() || !set.isEmpty() || !set1.isEmpty()) {
                serverPlayer.connection.send(new ClientboundUpdateAdvancementsPacket(this.isFirstPacket, set, set1, map));
            }
        }

        this.isFirstPacket = false;
    }

    public void setSelectedTab(@Nullable AdvancementHolder advancement) {
        AdvancementHolder advancementholder = this.lastSelectedTab;
        if (advancement != null && advancement.value().isRoot() && advancement.value().display().isPresent()) {
            this.lastSelectedTab = advancement;
        } else {
            this.lastSelectedTab = null;
        }

        if (advancementholder != this.lastSelectedTab) {
            this.player.connection.send(new ClientboundSelectAdvancementsTabPacket(this.lastSelectedTab == null ? null : this.lastSelectedTab.id()));
        }
    }

    public AdvancementProgress getOrStartProgress(AdvancementHolder advancement) {
        AdvancementProgress advancementprogress = this.progress.get(advancement);
        if (advancementprogress == null) {
            advancementprogress = new AdvancementProgress();
            this.startProgress(advancement, advancementprogress);
        }

        return advancementprogress;
    }

    private void startProgress(AdvancementHolder advancement, AdvancementProgress advancementProgress) {
        advancementProgress.update(advancement.value().requirements());
        this.progress.put(advancement, advancementProgress);
    }

    private void updateTreeVisibility(AdvancementNode root, Set<AdvancementHolder> advancementOutput, Set<ResourceLocation> idOutput) {
        AdvancementVisibilityEvaluator.evaluateVisibility(
            root, p_300726_ -> this.getOrStartProgress(p_300726_.holder()).isDone(), (p_300729_, p_300730_) -> {
                AdvancementHolder advancementholder = p_300729_.holder();
                if (p_300730_) {
                    if (this.visible.add(advancementholder)) {
                        advancementOutput.add(advancementholder);
                        if (this.progress.containsKey(advancementholder)) {
                            this.progressChanged.add(advancementholder);
                        }
                    }
                } else if (this.visible.remove(advancementholder)) {
                    idOutput.add(advancementholder.id());
                }
            }
        );
    }

    static record Data(Map<ResourceLocation, AdvancementProgress> map) {
        public static final Codec<PlayerAdvancements.Data> CODEC = Codec.unboundedMap(ResourceLocation.CODEC, AdvancementProgress.CODEC)
            .xmap(PlayerAdvancements.Data::new, PlayerAdvancements.Data::map);

        public void forEach(BiConsumer<ResourceLocation, AdvancementProgress> action) {
            this.map.entrySet().stream().sorted(Entry.comparingByValue()).forEach(p_301323_ -> action.accept(p_301323_.getKey(), p_301323_.getValue()));
        }
    }
}
