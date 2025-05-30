<template>
  <div v-if="section && fetchState" class="h-100 d-flex flex-column">
    <edit-toolbar v-bind="toolbarAttrs">
      <div class="status-container ml-1 mr-1">
        <s-status-selection v-model="section.status" :readonly="true" />
      </div>
      <s-assignee-selection
        v-model="section.assignee"
        :selectable-users="fieldAttrsHistoric.selectableUsers"
        :readonly="true"
        class="ml-1 mr-1"
      />

      <s-btn-secondary
        v-if="currentUrl"
        :to="currentUrl" exact
        class="ml-1 mr-1 d-none d-lg-inline-flex"
        prepend-icon="mdi-undo"
        text="Close Version History"
      />
      <btn-comments v-model="localSettings.reportingCommentSidebarVisible" :comments="fieldAttrsCurrent.collab.comments" />
      <btn-history v-model="historyVisible" />
    </edit-toolbar>

    <history-timeline-project
      v-model="historyVisible"
      :project="fetchState.projectHistoric"
      :section="section"
      :current-url="currentUrl"
    />

    <comment-sidebar
      ref="commentSidebarRef"
      :project="fetchState.projectCurrent"
      :project-type="fetchState.projectTypeCurrent"
      :section-id="route.params.sectionId as string"
      :readonly="fieldAttrsCurrent.readonly"
    />

    <v-container fluid class="pt-0 flex-grow-height overflow-y-auto">
      <v-row class="mt-0">
        <v-col cols="6" class="pb-0">
          <h2 class="text-h5 text-center">Historic Version <chip-date :value="(route.params.historyDate as string)" /></h2>
        </v-col>
        <v-col cols="6" class="pb-0">
          <h2 class="text-h5 text-center">Current Version</h2>
        </v-col>
      </v-row>
      <dynamic-input-field-diff 
        v-for="f in diffFieldProps" :key="f.id"
        v-bind="f"
      />
    </v-container>
  </div>
</template>

<script setup lang="ts">
import type { CommentSidebar } from '#components';

const localSettings = useLocalSettings();
const route = useRoute();
const projectStore = useProjectStore();

const { obj: section, fetchState, toolbarAttrs, fieldAttrsHistoric, fieldAttrsCurrent } = await useProjectHistory<ReportSection>({
  subresourceUrlPart: `/sections/${route.params.sectionId}/`,
  useCollab: (project: PentestProject) => projectStore.useReportingCollab({ project, sectionId: route.params.sectionId as string }),
});
const diffFieldProps = computed(() => formatHistoryObjectFieldProps({
  historic: {
    value: fetchState.value.dataHistoric?.data,
    definition: fetchState.value.projectTypeHistoric?.report_sections.find(s => s.id === route.params.sectionId)?.fields,
    attrs: fieldAttrsHistoric.value,
  },
  current: {
    value: fetchState.value.dataCurrent?.data,
    definition: fetchState.value?.projectTypeCurrent?.report_sections.find(s => s.id === route.params.sectionId)?.fields,
    attrs: {
      ...fieldAttrsCurrent.value,
      collab: collabSubpath(fieldAttrsCurrent.value.collab, 'data'),
      onComment: commentSidebarRef.value?.onCommentEvent,
    },
  },
}));

const commentSidebarRef = useTemplateRef<InstanceType<typeof CommentSidebar>>('commentSidebarRef');
const historyVisible = ref(false);
const currentUrl = computed(() => {
  if (section.value && projectStore.sections(section.value.project).map(s => s.id).includes(section.value.id)) {
    return `/projects/${section.value.project}/reporting/sections/${section.value.id}/`;
  }
  return null;
});
</script>

<style lang="scss" scoped>
.status-container {
  width: 15em;
}
.assignee-container {
  width: 17em;
}
</style>
