const FEISHU_URL = 'https://bcna3u8mz4uk.feishu.cn/docx/ILlBdMSP0ojCPVxfSIQcOVOFnbb'

export default function InterviewHandbook() {
  return (
    <div className="h-full">
      <iframe
        src={FEISHU_URL}
        title="面试手册 · 飞书文档"
        className="w-full h-full"
        style={{ border: 'none', minHeight: 600 }}
      />
    </div>
  )
}
