import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Select,
  message,
  Popconfirm,
  Avatar,
  Spin,
  Empty,
  Input,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  QrcodeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  EditOutlined,
} from '@ant-design/icons'
import { accountApi } from '../services/api'

interface Account {
  id: number
  platform: string
  username: string
  nickname: string
  avatar_url: string
  status: string
  created_at: string
  updated_at: string
  last_login_at: string
}

interface QRCodeSession {
  sessionId: string
  platform: string
  qrcodeUrl: string
  status: string
}

const platformOptions = [
  { value: 'douyin', label: '抖音' },
  { value: 'weixin', label: '视频号' },
  { value: 'xiaohongshu', label: '小红书' },
]

const Accounts: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)
  const [qrModalVisible, setQrModalVisible] = useState(false)
  const [qrSession, setQrSession] = useState<QRCodeSession | null>(null)
  const [selectedPlatform, setSelectedPlatform] = useState('douyin')
  const [qrLoading, setQrLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [editNickname, setEditNickname] = useState('')
  const [checkingId, setCheckingId] = useState<number | null>(null)

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (qrSession && qrSession.status === 'waiting') {
      interval = setInterval(checkQRCodeStatus, 2000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [qrSession])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const data = await accountApi.getAccounts() as Account[]
      setAccounts(data)
    } catch (error: unknown) {
      message.error((error as Error).message || '加载账号列表失败')
    } finally {
      setLoading(false)
    }
  }

  const generateQRCode = async () => {
    try {
      setQrLoading(true)
      const data = await accountApi.generateQRCode(selectedPlatform) as {
        qrcode_url: string
        session_id: string
        platform: string
      }
      setQrSession({
        sessionId: data.session_id,
        platform: data.platform,
        qrcodeUrl: data.qrcode_url,
        status: 'waiting',
      })
    } catch (error: unknown) {
      message.error((error as Error).message || '生成二维码失败')
    } finally {
      setQrLoading(false)
    }
  }

  const checkQRCodeStatus = async () => {
    if (!qrSession) return

    try {
      const data = await accountApi.checkQRCodeStatus(qrSession.sessionId) as {
        status: string
        account_id?: number
        message?: string
      }

      setQrSession(prev => prev ? { ...prev, status: data.status } : null)

      if (data.status === 'confirmed') {
        message.success('登录成功！')
        setQrModalVisible(false)
        setQrSession(null)
        loadAccounts()
      } else if (data.status === 'expired') {
        message.warning('二维码已过期，请刷新')
      }
    } catch (error) {
      // 忽略轮询错误
    }
  }

  const refreshQRCode = async () => {
    if (!qrSession) return

    try {
      setQrLoading(true)
      const data = await accountApi.refreshQRCode(qrSession.sessionId) as {
        qrcode_url: string
        session_id: string
        platform: string
      }
      setQrSession({
        sessionId: data.session_id,
        platform: data.platform,
        qrcodeUrl: data.qrcode_url,
        status: 'waiting',
      })
    } catch (error: unknown) {
      message.error((error as Error).message || '刷新二维码失败')
    } finally {
      setQrLoading(false)
    }
  }

  const deleteAccount = async (id: number) => {
    try {
      await accountApi.deleteAccount(id)
      message.success('删除成功')
      loadAccounts()
    } catch (error: unknown) {
      message.error((error as Error).message || '删除失败')
    }
  }

  const checkAccountStatus = async (id: number) => {
    try {
      setCheckingId(id)
      const data = await accountApi.checkAccountStatus(id) as {
        success: boolean
        message: string
      }
      if (data.success) {
        message.success(data.message)
      } else {
        message.warning(data.message)
      }
      loadAccounts()
    } catch (error: unknown) {
      message.error((error as Error).message || '检查失败')
    } finally {
      setCheckingId(null)
    }
  }

  const openEditModal = (account: Account) => {
    setEditingAccount(account)
    setEditNickname(account.nickname)
    setEditModalVisible(true)
  }

  const saveNickname = async () => {
    if (!editingAccount) return

    try {
      await accountApi.updateAccount(editingAccount.id, { nickname: editNickname })
      message.success('修改成功')
      setEditModalVisible(false)
      loadAccounts()
    } catch (error: unknown) {
      message.error((error as Error).message || '修改失败')
    }
  }

  const getPlatformTag = (platform: string) => {
    const config: Record<string, { label: string; className: string }> = {
      douyin: { label: '抖音', className: 'platform-tag-douyin' },
      weixin: { label: '视频号', className: 'platform-tag-weixin' },
      xiaohongshu: { label: '小红书', className: 'platform-tag-xiaohongshu' },
    }
    const { label, className } = config[platform] || { label: platform, className: '' }
    return <Tag className={className}>{label}</Tag>
  }

  const getStatusTag = (status: string) => {
    const config: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
      active: { label: '活跃', color: 'success', icon: <CheckCircleOutlined /> },
      inactive: { label: '未登录', color: 'default', icon: <CloseCircleOutlined /> },
      expired: { label: '已过期', color: 'warning', icon: <ExclamationCircleOutlined /> },
      banned: { label: '被封禁', color: 'error', icon: <CloseCircleOutlined /> },
    }
    const { label, color, icon } = config[status] || { label: status, color: 'default', icon: null }
    return <Tag color={color} icon={icon}>{label}</Tag>
  }

  const columns = [
    {
      title: '头像',
      dataIndex: 'avatar_url',
      key: 'avatar',
      width: 80,
      render: (url: string) => (
        <Avatar src={url} icon={<QrcodeOutlined />} size={40} />
      ),
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      ellipsis: true,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 100,
      render: getPlatformTag,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: getStatusTag,
    },
    {
      title: '最后登录',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      width: 180,
      render: (text: string) => text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: unknown, record: Account) => (
        <Space>
          <Tooltip title="编辑昵称">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openEditModal(record)}
            />
          </Tooltip>
          <Tooltip title="检查状态">
            <Button
              type="text"
              icon={<ReloadOutlined spin={checkingId === record.id} />}
              onClick={() => checkAccountStatus(record.id)}
              loading={checkingId === record.id}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此账号？"
            onConfirm={() => deleteAccount(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="fade-in">
      <Card
        title="账号管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadAccounts}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setQrModalVisible(true)}
            >
              添加账号
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={accounts}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 个账号`,
          }}
        />
      </Card>

      {/* 扫码登录弹窗 */}
      <Modal
        title="扫码登录"
        open={qrModalVisible}
        onCancel={() => {
          setQrModalVisible(false)
          setQrSession(null)
        }}
        footer={null}
        width={400}
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          {!qrSession ? (
            <>
              <div style={{ marginBottom: 20 }}>
                <span style={{ marginRight: 8 }}>选择平台：</span>
                <Select
                  value={selectedPlatform}
                  onChange={setSelectedPlatform}
                  options={platformOptions}
                  style={{ width: 120 }}
                />
              </div>
              <Button
                type="primary"
                size="large"
                icon={<QrcodeOutlined />}
                onClick={generateQRCode}
                loading={qrLoading}
              >
                生成二维码
              </Button>
            </>
          ) : (
            <>
              <div style={{ marginBottom: 16 }}>
                {getPlatformTag(qrSession.platform)}
              </div>
              <Spin spinning={qrLoading}>
                {qrSession.qrcodeUrl ? (
                  <img
                    src={qrSession.qrcodeUrl}
                    alt="登录二维码"
                    style={{
                      width: 256,
                      height: 256,
                      border: '1px solid #f0f0f0',
                      borderRadius: 8,
                    }}
                  />
                ) : (
                  <Empty description="二维码加载中..." />
                )}
              </Spin>
              <div style={{ marginTop: 16 }}>
                {qrSession.status === 'waiting' && (
                  <Tag color="processing">请使用手机APP扫描二维码</Tag>
                )}
                {qrSession.status === 'scanned' && (
                  <Tag color="success">已扫描，请在手机上确认</Tag>
                )}
                {qrSession.status === 'expired' && (
                  <>
                    <Tag color="error">二维码已过期</Tag>
                    <Button
                      type="link"
                      onClick={refreshQRCode}
                      loading={qrLoading}
                    >
                      点击刷新
                    </Button>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* 编辑昵称弹窗 */}
      <Modal
        title="编辑昵称"
        open={editModalVisible}
        onOk={saveNickname}
        onCancel={() => setEditModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Input
          value={editNickname}
          onChange={e => setEditNickname(e.target.value)}
          placeholder="请输入昵称"
        />
      </Modal>
    </div>
  )
}

export default Accounts
