package net.minecraft.advancements;

import com.google.common.collect.ImmutableMap;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.mojang.serialization.codecs.RecordCodecBuilder.Instance;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.critereon.CriterionValidator;
import net.minecraft.core.HolderGetter;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.ComponentUtils;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ItemLike;

public record Advancement(
    Optional<ResourceLocation> parent,
    Optional<DisplayInfo> display,
    AdvancementRewards rewards,
    Map<String, Criterion<?>> criteria,
    AdvancementRequirements requirements,
    boolean sendsTelemetryEvent,
    Optional<Component> name
) {
    private static final Codec<Map<String, Criterion<?>>> CRITERIA_CODEC = Codec.unboundedMap(Codec.STRING, Criterion.CODEC)
        .validate(p_311380_ -> p_311380_.isEmpty() ? DataResult.error(() -> "Advancement criteria cannot be empty") : DataResult.success(p_311380_));
    public static final Codec<Advancement> CODEC = RecordCodecBuilder.<Advancement>create(
            p_337334_ -> p_337334_.group(
                        ResourceLocation.CODEC.optionalFieldOf("parent").forGetter(Advancement::parent),
                        DisplayInfo.CODEC.optionalFieldOf("display").forGetter(Advancement::display),
                        AdvancementRewards.CODEC.optionalFieldOf("rewards", AdvancementRewards.EMPTY).forGetter(Advancement::rewards),
                        CRITERIA_CODEC.fieldOf("criteria").forGetter(Advancement::criteria),
                        AdvancementRequirements.CODEC.optionalFieldOf("requirements").forGetter(p_311389_ -> Optional.of(p_311389_.requirements())),
                        Codec.BOOL.optionalFieldOf("sends_telemetry_event", Boolean.valueOf(false)).forGetter(Advancement::sendsTelemetryEvent)
                    )
                    .apply(p_337334_, (p_311374_, p_311375_, p_311376_, p_311377_, p_311378_, p_311379_) -> {
                        AdvancementRequirements advancementrequirements = p_311378_.orElseGet(() -> AdvancementRequirements.allOf(p_311377_.keySet()));
                        return new Advancement(p_311374_, p_311375_, p_311376_, p_311377_, advancementrequirements, p_311379_);
                    })
        )
        .validate(Advancement::validate);
    public static final StreamCodec<RegistryFriendlyByteBuf, Advancement> STREAM_CODEC = StreamCodec.ofMember(Advancement::write, Advancement::read);
    public static final Codec<Optional<net.neoforged.neoforge.common.conditions.WithConditions<Advancement>>> CONDITIONAL_CODEC = net.neoforged.neoforge.common.conditions.ConditionalOps.createConditionalCodecWithConditions(CODEC);

    public Advancement(
        Optional<ResourceLocation> p_300893_,
        Optional<DisplayInfo> p_301147_,
        AdvancementRewards p_286389_,
        Map<String, Criterion<?>> p_286635_,
        AdvancementRequirements p_301002_,
        boolean p_286478_
    ) {
        this(p_300893_, p_301147_, p_286389_, Map.copyOf(p_286635_), p_301002_, p_286478_, p_301147_.map(Advancement::decorateName));
    }

    private static DataResult<Advancement> validate(Advancement advancement) {
        return advancement.requirements().validate(advancement.criteria().keySet()).map(p_311382_ -> advancement);
    }

    private static Component decorateName(DisplayInfo display) {
        Component component = display.getTitle();
        ChatFormatting chatformatting = display.getType().getChatColor();
        Component component1 = ComponentUtils.mergeStyles(component.copy(), Style.EMPTY.withColor(chatformatting))
            .append("\n")
            .append(display.getDescription());
        Component component2 = component.copy().withStyle(p_138316_ -> p_138316_.withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, component1)));
        return ComponentUtils.wrapInSquareBrackets(component2).withStyle(chatformatting);
    }

    public static Component name(AdvancementHolder advancement) {
        return advancement.value().name().orElseGet(() -> Component.literal(advancement.id().toString()));
    }

    private void write(RegistryFriendlyByteBuf buffer) {
        buffer.writeOptional(this.parent, FriendlyByteBuf::writeResourceLocation);
        DisplayInfo.STREAM_CODEC.apply(ByteBufCodecs::optional).encode(buffer, this.display);
        this.requirements.write(buffer);
        buffer.writeBoolean(this.sendsTelemetryEvent);
    }

    private static Advancement read(RegistryFriendlyByteBuf buffer) {
        return new Advancement(
            buffer.readOptional(FriendlyByteBuf::readResourceLocation),
            (Optional<DisplayInfo>)DisplayInfo.STREAM_CODEC.apply(ByteBufCodecs::optional).decode(buffer),
            AdvancementRewards.EMPTY,
            Map.of(),
            new AdvancementRequirements(buffer),
            buffer.readBoolean()
        );
    }

    public boolean isRoot() {
        return this.parent.isEmpty();
    }

    public void validate(ProblemReporter reporter, HolderGetter.Provider lootData) {
        this.criteria.forEach((p_335153_, p_335154_) -> {
            CriterionValidator criterionvalidator = new CriterionValidator(reporter.forChild(p_335153_), lootData);
            p_335154_.triggerInstance().validate(criterionvalidator);
        });
    }

    public static class Builder implements net.neoforged.neoforge.common.extensions.IAdvancementBuilderExtension {
        private Optional<ResourceLocation> parent = Optional.empty();
        private Optional<DisplayInfo> display = Optional.empty();
        private AdvancementRewards rewards = AdvancementRewards.EMPTY;
        private final ImmutableMap.Builder<String, Criterion<?>> criteria = ImmutableMap.builder();
        private Optional<AdvancementRequirements> requirements = Optional.empty();
        private AdvancementRequirements.Strategy requirementsStrategy = AdvancementRequirements.Strategy.AND;
        private boolean sendsTelemetryEvent;

        public static Advancement.Builder advancement() {
            return new Advancement.Builder().sendsTelemetryEvent();
        }

        public static Advancement.Builder recipeAdvancement() {
            return new Advancement.Builder();
        }

        public Advancement.Builder parent(AdvancementHolder parent) {
            this.parent = Optional.of(parent.id());
            return this;
        }

        @Deprecated(
            forRemoval = true
        )
        public Advancement.Builder parent(ResourceLocation parentId) {
            this.parent = Optional.of(parentId);
            return this;
        }

        public Advancement.Builder display(
            ItemStack icon,
            Component title,
            Component description,
            @Nullable ResourceLocation background,
            AdvancementType type,
            boolean showToast,
            boolean announceChat,
            boolean hidden
        ) {
            return this.display(new DisplayInfo(icon, title, description, Optional.ofNullable(background), type, showToast, announceChat, hidden));
        }

        public Advancement.Builder display(
            ItemLike icon,
            Component title,
            Component description,
            @Nullable ResourceLocation background,
            AdvancementType type,
            boolean showToast,
            boolean announceChat,
            boolean hidden
        ) {
            return this.display(
                new DisplayInfo(
                    new ItemStack(icon.asItem()), title, description, Optional.ofNullable(background), type, showToast, announceChat, hidden
                )
            );
        }

        public Advancement.Builder display(DisplayInfo display) {
            this.display = Optional.of(display);
            return this;
        }

        public Advancement.Builder rewards(AdvancementRewards.Builder rewardsBuilder) {
            return this.rewards(rewardsBuilder.build());
        }

        public Advancement.Builder rewards(AdvancementRewards rewards) {
            this.rewards = rewards;
            return this;
        }

        public Advancement.Builder addCriterion(String key, Criterion<?> criterion) {
            this.criteria.put(key, criterion);
            return this;
        }

        public Advancement.Builder requirements(AdvancementRequirements.Strategy requirementsStrategy) {
            this.requirementsStrategy = requirementsStrategy;
            return this;
        }

        public Advancement.Builder requirements(AdvancementRequirements requirements) {
            this.requirements = Optional.of(requirements);
            return this;
        }

        public Advancement.Builder sendsTelemetryEvent() {
            this.sendsTelemetryEvent = true;
            return this;
        }

        public AdvancementHolder build(ResourceLocation id) {
            Map<String, Criterion<?>> map = this.criteria.buildOrThrow();
            AdvancementRequirements advancementrequirements = this.requirements.orElseGet(() -> this.requirementsStrategy.create(map.keySet()));
            return new AdvancementHolder(
                id, new Advancement(this.parent, this.display, this.rewards, map, advancementrequirements, this.sendsTelemetryEvent)
            );
        }

        public AdvancementHolder save(Consumer<AdvancementHolder> output, String id) {
            AdvancementHolder advancementholder = this.build(ResourceLocation.parse(id));
            output.accept(advancementholder);
            return advancementholder;
        }
    }
}
