from app import create_app
from app.models import Activity
app = create_app()
with app.app_context():
    activity = Activity.query.filter_by(type='quiz').first()
    if activity:
        print('标题:', activity.title)
        print('内容:', activity.content)
    else:
        print('未找到测验活动')
