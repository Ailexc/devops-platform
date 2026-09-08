<template>
  <div class="interview">
    <iframe
      class="iv-frame"
      :src="docUrl"
      title="面试手册"
      allowfullscreen
    ></iframe>
  </div>
</template>

<script>
export default {
  name: 'InterviewGuide',
  data() {
    return {
      // 飞书面试手册文档（Chrome 等常规浏览器可直接内嵌展示）
      docUrl: 'https://bcna3u8mz4uk.feishu.cn/docx/ZsALd3O4Co0s2ixQsTpcjgzXnGd?from=from_copylink',
    }
  },
}
</script>

<style scoped>
.interview {
  height: calc(100vh - 118px); /* header(~52px) + tab-bar(~44px) + .ct padding(22px) */
}
.iv-frame {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
  border-radius: var(--radius);
  background: var(--card);
}
</style>
