import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Input,
  Upload,
  Form,
  message,
  Popconfirm,
  Checkbox,
  Row,
  Col,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  UploadOutlined,
  EditOutlined,
  TagsOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { contentApi } from '../services/api'

const { TextArea } = Input

interface Content {
  id: number
  title: string
  description: string
  tags: string[]
  video_path: string
  cover_path: string
  created_at: string
  updated_at: string
}

const Contents: React.FC = () => {
  const [contents, setContents] = useState<Content[]>([])
  const [loading, setLoading] = useState(false)
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [batchTitleModalVisible, setBatchTitleModalVisible] = useState(false)
  const [batchTagsModalVisible, setBatchTagsModalVisible] = useState(false)
  const [batchDescModalVisible, setBatchDescModalVisible] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [editingContent, setEditingContent] = useState<Content | null>(null)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [batchTitleForm] = Form.useForm()
  const [batchTagsForm] = Form.useForm()
  const [batchDescForm] = Form.useForm()

  useEffect(() => {
    loadContents()
  }, [])

  const loadContents = async () => {
    try {
      setLoading(true)
      const data = await contentApi.getContents() as Content[]
      setContents(data)
    } catch (error: unknown) {
      message.error((error as Error).message || '加载内容列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请选择要上传的视频')
      return
    }

    try {
      setUploading(true)
      const values = await form.validateFields()

      const formData = new FormData()
      fileList.forEach(file => {
        if (file.originFileObj) {
          formData.append('files', file.originFileObj)
        }
      })

      // 为每个视频创建标题
      const titles = fileList.map((file, index) => {
        if (values.titleTemplate) {
          return values.titleTemplate.replace('{index}', String(index + 1))
        }
        return file.name.replace(/\.[^/.]+$/, '')
      })
      formData.append('titles', JSON.stringify(titles))

      // 统一描述
      if (values.description) {
        const descriptions = fileList.map(() => values.description)
        formData.append('descriptions', JSON.stringify(descriptions))
      }

      // 统一标签
      if (values.tags) {
        const tagList = values.tags.split(/[,，\s]+/).filter(Boolean)
        const tagsArray = fileList.map(() => tagList)
        formData.append('tags', JSON.stringify(tagsArray))
      }

      const result = await contentApi.uploadVideos(formData) as {
        success: boolean
        message: string
      }
      message.success(result.message)
      setUploadModalVisible(false)
      setFileList([])
      form.resetFields()
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const openEditModal = (content: Content) => {
    setEditingContent(content)
    editForm.setFieldsValue({
      title: content.title,
      description: content.description,
      tags: content.tags?.join(', '),
    })
    setEditModalVisible(true)
  }

  const handleEdit = async () => {
    if (!editingContent) return

    try {
      const values = await editForm.validateFields()
      const tags = values.tags ? values.tags.split(/[,，\s]+/).filter(Boolean) : []

      await contentApi.updateContent(editingContent.id, {
        title: values.title,
        description: values.description,
        tags,
      })

      message.success('修改成功')
      setEditModalVisible(false)
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '修改失败')
    }
  }

  const deleteContent = async (id: number) => {
    try {
      await contentApi.deleteContent(id)
      message.success('删除成功')
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '删除失败')
    }
  }

  const batchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的内容')
      return
    }

    try {
      await contentApi.batchDelete(selectedRowKeys)
      message.success('批量删除成功')
      setSelectedRowKeys([])
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '批量删除失败')
    }
  }

  const handleBatchUpdateTitle = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要修改的内容')
      return
    }

    try {
      const values = await batchTitleForm.validateFields()
      await contentApi.batchUpdateTitle(selectedRowKeys, values.titleTemplate)
      message.success('批量修改标题成功')
      setBatchTitleModalVisible(false)
      batchTitleForm.resetFields()
      setSelectedRowKeys([])
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '批量修改失败')
    }
  }

  const handleBatchUpdateTags = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要修改的内容')
      return
    }

    try {
      const values = await batchTagsForm.validateFields()
      const tags = values.tags.split(/[,，\s]+/).filter(Boolean)
      await contentApi.batchUpdateTags(selectedRowKeys, tags)
      message.success('批量修改话题成功')
      setBatchTagsModalVisible(false)
      batchTagsForm.resetFields()
      setSelectedRowKeys([])
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '批量修改失败')
    }
  }

  const handleBatchUpdateDesc = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要修改的内容')
      return
    }

    try {
      const values = await batchDescForm.validateFields()
      await contentApi.batchUpdateDescription(selectedRowKeys, values.description)
      message.success('批量修改文案成功')
      setBatchDescModalVisible(false)
      batchDescForm.resetFields()
      setSelectedRowKeys([])
      loadContents()
    } catch (error: unknown) {
      message.error((error as Error).message || '批量修改失败')
    }
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '文案',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '话题',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: string[]) =>
        tags && tags.length > 0 ? (
          <Space wrap>
            {tags.slice(0, 3).map((tag, i) => (
              <Tag key={i} color="blue">
                #{tag}
              </Tag>
            ))}
            {tags.length > 3 && <Tag>+{tags.length - 3}</Tag>}
          </Space>
        ) : (
          '-'
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: unknown, record: Content) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title="确定删除此内容？"
            onConfirm={() => deleteContent(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys as number[]),
  }

  return (
    <div className="fade-in">
      <Card
        title="内容管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadContents}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传视频
            </Button>
          </Space>
        }
      >
        {selectedRowKeys.length > 0 && (
          <Row style={{ marginBottom: 16 }}>
            <Col>
              <Space>
                <Checkbox
                  checked={selectedRowKeys.length === contents.length}
                  indeterminate={
                    selectedRowKeys.length > 0 &&
                    selectedRowKeys.length < contents.length
                  }
                  onChange={e =>
                    setSelectedRowKeys(
                      e.target.checked ? contents.map(c => c.id) : []
                    )
                  }
                >
                  已选 {selectedRowKeys.length} 项
                </Checkbox>
                <Button
                  icon={<EditOutlined />}
                  onClick={() => setBatchTitleModalVisible(true)}
                >
                  批量改标题
                </Button>
                <Button
                  icon={<TagsOutlined />}
                  onClick={() => setBatchTagsModalVisible(true)}
                >
                  批量改话题
                </Button>
                <Button
                  icon={<FileTextOutlined />}
                  onClick={() => setBatchDescModalVisible(true)}
                >
                  批量改文案
                </Button>
                <Popconfirm
                  title={`确定删除选中的 ${selectedRowKeys.length} 项内容？`}
                  onConfirm={batchDelete}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button danger icon={<DeleteOutlined />}>
                    批量删除
                  </Button>
                </Popconfirm>
              </Space>
            </Col>
          </Row>
        )}

        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={contents}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 个内容`,
          }}
        />
      </Card>

      {/* 上传视频弹窗 */}
      <Modal
        title="上传视频"
        open={uploadModalVisible}
        onOk={handleUpload}
        onCancel={() => {
          setUploadModalVisible(false)
          setFileList([])
          form.resetFields()
        }}
        okText="上传"
        cancelText="取消"
        confirmLoading={uploading}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="选择视频文件" required>
            <Upload.Dragger
              multiple
              accept="video/*"
              fileList={fileList}
              beforeUpload={file => {
                setFileList(prev => [...prev, file as unknown as UploadFile])
                return false
              }}
              onRemove={file => {
                setFileList(prev => prev.filter(f => f.uid !== file.uid))
              }}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽视频到此处上传</p>
              <p className="ant-upload-hint">支持批量上传多个视频文件</p>
            </Upload.Dragger>
          </Form.Item>

          <Form.Item
            name="titleTemplate"
            label="标题模板"
            extra="使用 {index} 作为序号占位符，如：精彩视频 {index}"
          >
            <Input placeholder="留空则使用文件名作为标题" />
          </Form.Item>

          <Form.Item
            name="tags"
            label="话题标签"
            extra="多个标签用逗号或空格分隔"
          >
            <Input placeholder="例如：生活,日常,记录" />
          </Form.Item>

          <Form.Item name="description" label="文案描述">
            <TextArea rows={4} placeholder="输入视频描述文案" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑内容弹窗 */}
      <Modal
        title="编辑内容"
        open={editModalVisible}
        onOk={handleEdit}
        onCancel={() => setEditModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="tags"
            label="话题标签"
            extra="多个标签用逗号或空格分隔"
          >
            <Input placeholder="例如：生活,日常,记录" />
          </Form.Item>
          <Form.Item name="description" label="文案描述">
            <TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量修改标题弹窗 */}
      <Modal
        title="批量修改标题"
        open={batchTitleModalVisible}
        onOk={handleBatchUpdateTitle}
        onCancel={() => setBatchTitleModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={batchTitleForm} layout="vertical">
          <Form.Item
            name="titleTemplate"
            label="标题模板"
            rules={[{ required: true, message: '请输入标题模板' }]}
            extra="使用 {index} 作为序号占位符"
          >
            <Input placeholder="例如：精彩视频第{index}集" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量修改话题弹窗 */}
      <Modal
        title="批量修改话题"
        open={batchTagsModalVisible}
        onOk={handleBatchUpdateTags}
        onCancel={() => setBatchTagsModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={batchTagsForm} layout="vertical">
          <Form.Item
            name="tags"
            label="话题标签"
            rules={[{ required: true, message: '请输入话题标签' }]}
            extra="多个标签用逗号或空格分隔"
          >
            <Input placeholder="例如：生活,日常,记录" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量修改文案弹窗 */}
      <Modal
        title="批量修改文案"
        open={batchDescModalVisible}
        onOk={handleBatchUpdateDesc}
        onCancel={() => setBatchDescModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={batchDescForm} layout="vertical">
          <Form.Item
            name="description"
            label="文案描述"
            rules={[{ required: true, message: '请输入文案' }]}
          >
            <TextArea rows={4} placeholder="输入视频描述文案" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Contents
