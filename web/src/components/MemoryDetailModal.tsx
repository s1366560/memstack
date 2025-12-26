import React from 'react';
import { X, Brain, User, Calendar, Tag, Hash, Eye, Edit3, Share2, Download } from 'lucide-react';
import { Memory } from '../types/memory';

interface MemoryDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  memory: Memory | null;
}

export const MemoryDetailModal: React.FC<MemoryDetailModalProps> = ({
  isOpen,
  onClose,
  memory
}) => {
  if (!isOpen || !memory) return null;

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'text': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      case 'document': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
      case 'image': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300';
      case 'video': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-slate-200';
    }
  };

  const handleEdit = () => {
    // TODO: Implement edit functionality
    console.log('Edit memory:', memory.id);
  };

  const handleShare = () => {
    // TODO: Implement share functionality
    console.log('Share memory:', memory.id);
  };

  const handleDownload = () => {
    const data = JSON.stringify(memory, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `memory-${memory.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">记忆详情</h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleEdit}
              className="p-2 text-gray-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 rounded-md transition-colors"
              title="编辑"
            >
              <Edit3 className="h-4 w-4" />
            </button>
            <button
              onClick={handleShare}
              className="p-2 text-gray-400 dark:text-slate-500 hover:text-green-600 dark:hover:text-green-400 rounded-md transition-colors"
              title="分享"
            >
              <Share2 className="h-4 w-4" />
            </button>
            <button
              onClick={handleDownload}
              className="p-2 text-gray-400 dark:text-slate-500 hover:text-purple-600 dark:hover:text-purple-400 rounded-md transition-colors"
              title="下载"
            >
              <Download className="h-4 w-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 rounded-md transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-6">
            <div className="mb-6">
              <div className="flex items-center space-x-3 mb-3">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTypeColor(memory.content_type)}`}>
                  {memory.content_type}
                </span>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">{memory.title}</h3>
              </div>
              
              <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-slate-400 mb-4">
                {memory.author_id && (
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>用户: {memory.author_id}</span>
                  </div>
                )}
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>创建: {formatDate(memory.created_at)}</span>
                </div>
                {memory.updated_at !== memory.created_at && (
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-4 w-4" />
                    <span>更新: {formatDate(memory.updated_at || '')}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="mb-6">
              <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-3">记忆内容</h4>
              <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-4 border border-gray-100 dark:border-slate-700">
                <p className="text-gray-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">{memory.content}</p>
              </div>
            </div>

            {memory.entities && memory.entities.length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-3">实体信息</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {memory.entities.map((entity, index) => (
                    <div key={index} className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/30 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-1">
                        <Hash className="h-4 w-4 text-green-600 dark:text-green-400" />
                        <span className="font-medium text-green-800 dark:text-green-200">{entity.name}</span>
                        <span className="text-xs text-green-600 dark:text-green-300 bg-green-100 dark:bg-green-900/40 px-2 py-1 rounded-full">
                          {entity.type}
                        </span>
                      </div>
                      {entity.properties && Object.keys(entity.properties).length > 0 && (
                        <p className="text-sm text-green-700 dark:text-green-300">{JSON.stringify(entity.properties)}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {memory.relationships && memory.relationships.length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-3">关系信息</h4>
                <div className="space-y-3">
                  {memory.relationships.map((relationship, index) => (
                    <div key={index} className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-900/30 rounded-lg p-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-purple-800 dark:text-purple-200">{relationship.source_id}</span>
                            <span className="text-purple-600 dark:text-purple-400">→</span>
                            <span className="font-medium text-purple-800 dark:text-purple-200">{relationship.target_id}</span>
                          </div>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-xs text-purple-600 dark:text-purple-300 bg-purple-100 dark:bg-purple-900/40 px-2 py-1 rounded-full">
                              {relationship.type}
                            </span>
                            {relationship.confidence && (
                              <span className="text-xs text-purple-500 dark:text-purple-400">
                                置信度: {relationship.confidence}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      {relationship.properties && Object.keys(relationship.properties).length > 0 && (
                        <p className="text-sm text-purple-700 dark:text-purple-300 mt-2">{JSON.stringify(relationship.properties)}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {memory.metadata && Object.keys(memory.metadata).length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-3">元数据</h4>
                <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-4 border border-gray-100 dark:border-slate-700">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(memory.metadata).map(([key, value]) => (
                      <div key={key} className="flex items-center space-x-2">
                        <Tag className="h-4 w-4 text-gray-400 dark:text-slate-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-slate-300">{key}:</span>
                        <span className="text-sm text-gray-600 dark:text-slate-400">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div className="border-t border-gray-200 dark:border-slate-800 pt-4">
              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-slate-400">
                <div className="flex items-center space-x-4">
                  <span>ID: {memory.id}</span>
                  <span>项目: {memory.project_id}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Eye className="h-4 w-4" />
                  <span>查看次数: {memory.metadata?.view_count || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
