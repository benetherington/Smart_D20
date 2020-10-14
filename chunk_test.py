page_length = 6

def chunk_with_pagination(to_chunk, chunked=None, page=None):
    '''
    Recursive function used to chunk up a raw list into pages.
    Returns a list of lists (pages), self.page_length long, with
    next and/or previous buttons at the ends.
    '''
    if chunked == None:
      chunked = []
    if page == None:
      page = 0
    buttons = []
    # decide if previous button is required
    if page > 0:
      buttons.append('previous')
    # decide if next button is required
    if len(to_chunk) > page_length-len(buttons):
      # add a next button
      buttons.append('next')
      # prepend menu items to fill up the rest of the spaces
      this_chunk = to_chunk[0:page_length-len(buttons)]
      chunked.append(this_chunk+buttons)
      del to_chunk[0:page_length-1]
      # get to work on the next page
      page += 1
      return chunk_with_pagination(to_chunk, chunked, page)
    else:
      # no next button is required, prepend the rest of the items
      chunked.append(to_chunk+buttons)
      # And we're done!
      return chunked


print( chunk_with_pagination([*range(3)]) )
print( chunk_with_pagination([*range(6)]) )
print( chunk_with_pagination([*range(7)]) )
print( chunk_with_pagination([*range(20)]) )