"""Rename milestones table to journeys and update foreign keys

Revision ID: 1da32c92ae33
Revises: 22d22edc25e9
Create Date: 2025-10-13 16:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1da32c92ae33'
down_revision: Union[str, None] = '22d22edc25e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. journeys 테이블이 존재하지 않는 경우에만 생성
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'journeys' not in inspector.get_table_names():
        op.create_table('journeys',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=100), nullable=False, comment='여정 제목'),
            sa.Column('description', sa.Text(), nullable=True, comment='여정 설명'),
            sa.Column('start_date', sa.Date(), nullable=False, comment='시작일'),
            sa.Column('end_date', sa.Date(), nullable=False, comment='종료일'),
            sa.Column('progress', sa.Float(), nullable=False, default=0.0, comment='진행률 (0-100)'),
            sa.Column('status', sa.Enum('PLANNING', 'ACTIVE', 'COMPLETED', 'PAUSED', name='journeystatus'), nullable=False, comment='여정 상태'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='생성일시'),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='수정일시'),
            sa.PrimaryKeyConstraint('id'),
            comment='여정 테이블'
        )

        # 2. 인덱스 생성
        op.create_index(op.f('ix_journeys_id'), 'journeys', ['id'], unique=False)

    # 3. milestones 테이블에서 데이터를 journeys 테이블로 복사 (중복 방지)
    if 'milestones' in inspector.get_table_names():
        op.execute("""
            INSERT OR IGNORE INTO journeys (
                id, title, description, start_date, end_date,
                progress, status, created_at, updated_at
            )
            SELECT
                id, title, description, start_date, end_date,
                progress, status, created_at, updated_at
            FROM milestones
        """)

    # 4. daily_todos 테이블의 milestone_id 컬럼을 journey_id로 변경 (batch mode 사용)
    daily_todos_columns = [col['name'] for col in inspector.get_columns('daily_todos')]

    if 'journey_id' not in daily_todos_columns:
        with op.batch_alter_table('daily_todos', schema=None) as batch_op:
            # 새 컬럼 추가
            batch_op.add_column(sa.Column('journey_id', sa.Integer(), nullable=True, comment='연관 여정 ID'))

    # 기존 데이터 복사 (milestone_id 컬럼이 있는 경우에만)
    if 'milestone_id' in daily_todos_columns and 'journey_id' in [col['name'] for col in inspector.get_columns('daily_todos')] + ['journey_id']:
        op.execute("UPDATE daily_todos SET journey_id = milestone_id WHERE milestone_id IS NOT NULL AND journey_id IS NULL")

    if 'milestone_id' in daily_todos_columns:
        with op.batch_alter_table('daily_todos', schema=None) as batch_op:
            # 기존 컬럼 삭제
            batch_op.drop_column('milestone_id')
            # 새 외래키 제약조건 추가
            batch_op.create_foreign_key('daily_todos_journey_id_fkey', 'journeys', ['journey_id'], ['id'])

    # 5. todos 테이블의 milestone_id 컬럼을 journey_id로 변경 (batch mode 사용)
    todos_columns = [col['name'] for col in inspector.get_columns('todos')]

    if 'journey_id' not in todos_columns:
        with op.batch_alter_table('todos', schema=None) as batch_op:
            # 새 컬럼 추가
            batch_op.add_column(sa.Column('journey_id', sa.Integer(), nullable=True, comment='여정 ID'))

    # 기존 데이터 복사 (milestone_id 컬럼이 있는 경우에만)
    if 'milestone_id' in todos_columns:
        op.execute("UPDATE todos SET journey_id = milestone_id WHERE milestone_id IS NOT NULL AND journey_id IS NULL")

    if 'milestone_id' in todos_columns:
        with op.batch_alter_table('todos', schema=None) as batch_op:
            # 기존 컬럼 삭제
            batch_op.drop_column('milestone_id')
            # 새 외래키 제약조건 추가
            batch_op.create_foreign_key('todos_journey_id_fkey', 'journeys', ['journey_id'], ['id'])

    # 6. 마지막으로 milestones 테이블 삭제 (존재하는 경우에만)
    if 'milestones' in inspector.get_table_names():
        op.drop_table('milestones')


def downgrade() -> None:
    # downgrade는 복잡한 롤백 과정이므로 기본적인 에러만 방지
    # 실제 롤백이 필요하면 백업에서 복원하는 것을 권장
    raise NotImplementedError("이 마이그레이션의 롤백은 백업에서 복원하는 것을 권장합니다. 'python scripts/db.py restore backup_file.db' 사용")