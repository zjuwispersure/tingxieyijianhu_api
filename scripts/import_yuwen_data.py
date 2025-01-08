import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'import_yuwen_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataImporter:
    """语文数据导入工具
    
    用于将Excel格式的语文学习项数据导入到数据库中
    """
    
    def __init__(self, db_url):
        """初始化导入工具
        
        Args:
            db_url: 数据库连接URL
        """
        self.engine = create_engine(db_url)
        self.required_columns = {
            'word': '字/词',
            'pinyin': '拼音',
            'type': '类型',
            'grade': '年级',
            'semester': '学期',
            'unit': '单元',
            'textbook_version': '教材版本'
        }
        
    def validate_file(self, file_path):
        """验证Excel文件格式
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            bool: 文件是否有效
            str: 错误信息（如果有）
        """
        try:
            if not os.path.exists(file_path):
                return False, f'文件不存在: {file_path}'
                
            df = pd.read_excel(file_path)
            
            # 检查必要列
            missing_columns = []
            for col, cn_name in self.required_columns.items():
                if cn_name not in df.columns:
                    missing_columns.append(f'{cn_name}({col})')
                    
            if missing_columns:
                return False, f'缺少必要列: {", ".join(missing_columns)}'
                
            return True, None
            
        except Exception as e:
            return False, f'验证文件失败: {str(e)}'
            
    def transform_data(self, df):
        """转换数据格式
        
        Args:
            df: pandas DataFrame
            
        Returns:
            DataFrame: 转换后的数据
        """
        # 列名映射
        column_map = {v: k for k, v in self.required_columns.items()}
        df = df.rename(columns=column_map)
        
        # 数据清理和转换
        df['grade'] = pd.to_numeric(df['grade'], errors='coerce')
        df['semester'] = pd.to_numeric(df['semester'], errors='coerce')
        df['unit'] = pd.to_numeric(df['unit'], errors='coerce')
        
        # 去除无效数据
        df = df.dropna(subset=['word', 'grade', 'semester', 'unit'])
        
        return df
        
    def import_data(self, file_path, batch_size=1000):
        """导入数据
        
        Args:
            file_path: Excel文件路径
            batch_size: 批量导入大小
            
        Returns:
            tuple: (成功数量, 错误信息)
        """
        try:
            # 验证文件
            is_valid, error = self.validate_file(file_path)
            if not is_valid:
                logger.error(f"文件验证失败: {error}")
                return 0, error
                
            # 读取数据
            logger.info(f"开始读取文件: {file_path}")
            df = pd.read_excel(file_path)
            
            # 转换数据
            df = self.transform_data(df)
            total_rows = len(df)
            logger.info(f"读取到 {total_rows} 条数据")
            
            # 批量导入
            success_count = 0
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]
                try:
                    batch.to_sql(
                        'yuwen_items',
                        self.engine,
                        if_exists='append',
                        index=False
                    )
                    success_count += len(batch)
                    logger.info(f"已导入 {success_count}/{total_rows} 条数据")
                except SQLAlchemyError as e:
                    logger.error(f"导入批次失败: {str(e)}")
                    continue
                    
            return success_count, None
            
        except Exception as e:
            error_msg = f"导入失败: {str(e)}"
            logger.error(f"{error_msg}\n", exc_info=True)
            return 0, error_msg

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python import_yuwen_data.py <excel_file>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    db_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    importer = DataImporter(db_url)
    success_count, error = importer.import_data(file_path)
    
    if error:
        logger.error(f"导入失败: {error}")
        sys.exit(1)
    else:
        logger.info(f"导入完成，成功导入 {success_count} 条数据")

if __name__ == '__main__':
    main() 