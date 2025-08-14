from unittest.mock import patch, Mock

from api_integration.comment_scraper import fetch_story_comments


SAMPLE_ITEM_HTML = """
<html>
 <body>
  <table>
   <tr class='athing comtr' id='c1'>
    <td class='ind'><img src='s.gif' width='0'></td>
    <td class='default'>
      <div class='comment'><span class='commtext'>Top level comment</span></div>
      <div class='comhead'>
        <a class='hnuser'>user1</a>
        <span class='age'><a href='item?id=c1'>2 hours ago</a></span>
        | <a href='item?id=p1'>parent</a>
      </div>
    </td>
   </tr>
   <tr class='athing comtr' id='c2'>
    <td class='ind'><img src='s.gif' width='40'></td>
    <td class='default'>
      <div class='comment'><span class='commtext'>Nested comment</span></div>
      <div class='comhead'>
        <a class='hnuser'>user2</a>
        <span class='age'><a href='item?id=c2'>30 minutes ago</a></span>
        | <a href='item?id=c1'>parent</a>
      </div>
    </td>
   </tr>
   <tr class='athing comtr' id='c3'>
    <td class='ind'><img src='s.gif' width='0'></td>
    <td class='default'>
      <div class='comhead'>
        <a class='hnuser'>user3</a>
        <span class='age'><a href='item?id=c3'>1 day ago</a></span>
        | <a href='item?id=p1'>parent</a>
      </div>
    </td>
   </tr>
  </table>
 </body>
 </html>
"""


@patch('requests.get')
def test_fetch_story_comments_parses_fields(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_ITEM_HTML
    mock_get.return_value = mock_response

    comments = fetch_story_comments('p1')

    assert isinstance(comments, list)
    assert len(comments) == 3

    c1 = comments[0]
    assert c1['id'] == 'c1'
    assert c1['author'] == 'user1'
    assert c1['text'] == 'Top level comment'
    assert c1['parent_id'] == 'p1'
    assert c1['depth'] == 0
    assert c1['age'] and 'hour' in c1['age']

    c2 = comments[1]
    assert c2['id'] == 'c2'
    assert c2['author'] == 'user2'
    assert c2['text'] == 'Nested comment'
    assert c2['parent_id'] == 'c1'
    assert c2['depth'] == 1

    c3 = comments[2]
    assert c3['id'] == 'c3'
    assert c3['author'] == 'user3'
    # deleted/dead-like comment has no commtext -> None
    assert c3['text'] is None
    assert c3['depth'] == 0


@patch('requests.get')
def test_fetch_story_comments_respects_depth_and_limit(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_ITEM_HTML
    mock_get.return_value = mock_response

    top_only = fetch_story_comments('p1', max_depth=0)
    assert all(c['depth'] == 0 for c in top_only)
    assert len(top_only) == 2  # c1 and c3

    limited = fetch_story_comments('p1', limit=1)
    assert len(limited) == 1


@patch('requests.get')
def test_fetch_story_comments_realistic_html(mock_get):
    realistic_item_html = """
    <!doctype html>
    <html><body>
      <table>
       <tr class='athing' id='100001'>
         <td class='title'><span class='titleline'><a href='https://example.com/a'>A title</a></span></td>
       </tr>
       <tr>
         <td class='subtext'>
           <span class='score' id='score_100001'>123 points</span>
           by <a href='user?id=alice' class='hnuser'>alice</a>
           <span class='age'><a href='item?id=100001'>2 hours ago</a></span>
           | <a href='item?id=100001'>42 comments</a>
         </td>
       </tr>
       <tr class='athing comtr' id='c1'>
         <td class='ind'><img src='s.gif' width='0'></td>
         <td class='default'>
           <div class='comment'><span class='commtext c00'>Top level comment</span></div>
           <div class='comhead'>
             <a class='hnuser'>user1</a>
             <span class='age'><a href='item?id=c1'>2 hours ago</a></span>
             | <a href='item?id=p1'>parent</a>
           </div>
         </td>
       </tr>
       <tr class='athing comtr' id='c2'>
         <td class='ind'><img src='s.gif' width='40'></td>
         <td class='default'>
           <div class='comment'><span class='commtext c00'>Nested comment</span></div>
           <div class='comhead'>
             <a class='hnuser'>user2</a>
             <span class='age'><a href='item?id=c2'>30 minutes ago</a></span>
             | <a href='item?id=c1'>parent</a>
           </div>
         </td>
       </tr>
      </table>
      </body></html>
    """

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = realistic_item_html
    mock_get.return_value = mock_response

    comments = fetch_story_comments('100001', max_depth=2)
    assert len(comments) == 2
    assert comments[0]['id'] == 'c1'
    assert comments[0]['author'] == 'user1'
    assert comments[0]['depth'] == 0
    assert comments[0]['text'] == 'Top level comment'
    assert comments[0]['parent_id'] == 'p1'

    assert comments[1]['id'] == 'c2'
    assert comments[1]['author'] == 'user2'
    assert comments[1]['depth'] == 1
    assert comments[1]['text'] == 'Nested comment'
    assert comments[1]['parent_id'] == 'c1'

