unicode_type = type(u"")
def ensure_unicode(data, encoding="utf8"):
    """
    Ensures that the given string is return as type ``unicode``.
    :type data: str or bytes
    :param data: String to convert if needed.
    :param str encoding: [opt] The encoding to use if needed..
    :returns: The given string as type ``unicode``.
    :rtype: str
    """
    return data.decode(encoding) if isinstance(data, bytes) else unicode_type(data)

class Property():
    def __init__(self):
        self.raw_dict={}
    
    def __setitem__(self, key, value):  # type: (str, str) -> None
        if value:
            self.raw_dict[key] = ensure_unicode(value)
        else:
            logger.debug("Ignoring empty property: '%s'", key)

    def _close(self, listitem):  # type: (xbmcgui.ListItem) -> None
        for key, value in self.raw_dict.items():
            listitem.setProperty(key, value)

class Listitem(object):
    """
    The “listitem” control is used for the creating "folder" or "video" items within Kodi.
    :param str content_type: [opt] Type of content been listed. e.g. "video", "music", "pictures".
    """
    def __getstate__(self):
        state = self.__dict__.copy()
        state["label"] = self.label
        del state["listitem"]
        return state

    def __setstate__(self, state):
        label = state.pop("label")
        self.__dict__.update(state)
        self.listitem = xbmcgui.ListItem()
        self.label = label

    def __init__(self, content_type="video"):
        self._content_type = content_type
        self._is_playable = False
        self._is_folder = False
        self._args = None
        self._path = ""

        #: List of paths to subtitle files.
        self.subtitles = []

        self.property = Property()
        """
        Dictionary like object that allows you to add "listitem properties". e.g. "StartOffset".
        Some of these are processed internally by Kodi, such as the "StartOffset" property,
        which is the offset in seconds at which to start playback of an item. Others may be used
        in the skin to add extra information, such as "WatchedCount" for tvshow items.
        :examples:
            >>> item = Listitem()
            >>> item.property['StartOffset'] = '256.4'
        """

    @property
    def label(self):  # type: () -> str
        """
        The listitem label property.
        :example:
            >>> item = Listitem()
            >>> item.label = "Video Title"
        """
        label = self.listitem.getLabel()
        return label.decode("utf8") if isinstance(label, bytes) else label

    @label.setter
    def label(self, label):  # type: (str) -> None
        self.listitem.setLabel(label)
        unformatted_label = strip_formatting("", label)
        self.params["_title_"] = unformatted_label
        self.info["title"] = unformatted_label

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        # For backwards compatibility
        self._path = value
        self._is_playable = True

    def set_path(self, path, is_folder=False, is_playable=True):
        """
        Set the listitem's path.
        The path can be any of the following:
            * Any kodi path, e.g. "plugin://" or "script://"
            * Directly playable URL or filepath.
        .. note::
            When specifying a external 'plugin' or 'script' as the path, Kodi will treat it as a playable item.
            To override this behavior, you can set the ``is_playable`` and ``is_folder`` parameters.
        :param path: A playable URL or plugin/script path.
        :param is_folder: Tells kodi if path is a folder (default -> ``False``).
        :param is_playable: Tells kodi if path is a playable item (default -> ``True``).
        """
        self._path = path
        self._is_folder = is_folder
        self._is_playable = False if path.startswith("script://") else is_playable

    def set_callback(self, callback, *args, **kwargs):
        """
        Set the "callback" function for this listitem.
        The "callback" parameter can be any of the following:
            * :class:`codequick.Script<codequick.script.Script>` callback.
            * :class:`codequick.Route<codequick.route.Route>` callback.
            * :class:`codequick.Resolver<codequick.resolver.Resolver>` callback.
            * A callback reference object :func:`Script.ref<codequick.script.Script.ref>`.
        :param callback: The "callback" function or reference object.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        """
        if hasattr(callback, "route"):
            callback = callback.route
        elif not isinstance(callback, CallbackRef):
            # We don't have a plugin / http path,
            # So we should then have a callback path
            if "://" not in callback:
                msg = "passing callback path to 'set_callback' is deprecated, " \
                      "use callback reference 'Route.ref' instead"
                logger.warning("DeprecationWarning: " + msg)
                callback = dispatcher.get_route(callback)
            else:
                msg = "passing a playable / plugin path to 'set_callback' is deprecated, use 'set_path' instead"
                logger.warning("DeprecationWarning: " + msg)
                is_folder = kwargs.pop("is_folder", False)
                is_playable = kwargs.pop("is_playable", not is_folder)
                self.set_path(callback, is_folder, is_playable)
                return

        self.params.update(kwargs)
        self._is_playable = callback.is_playable
        self._is_folder = callback.is_folder
        self._path = callback
        self._args = args

    # noinspection PyProtectedMember
    def build(self):
        listitem = self.listitem
        isfolder = self._is_folder
        listitem.setProperty("folder", str(isfolder).lower())
        listitem.setProperty("isplayable", str(self._is_playable).lower())

        if isinstance(self._path, CallbackRef):
            path = build_path(self._path, self._args, self.params.raw_dict)
        else:
            path = self._path

        if not isfolder:
            # Add mediatype if not already set
            if "mediatype" not in self.info.raw_dict and self._content_type in ("video", "music"):  # pragma: no branch
                self.info.raw_dict["mediatype"] = self._content_type

            # Set the listitem subtitles
            if self.subtitles:
                self.listitem.setSubtitles(self.subtitles)

            # Add Video Specific Context menu items
            self.context.append(("$LOCALIZE[13347]", "Action(Queue)"))
            self.context.append(("$LOCALIZE[13350]", "ActivateWindow(videoplaylist)"))

            # Close video related datasets
            self.stream._close(listitem)

        # Set label to UNKNOWN if unset
        if not self.label:  # pragma: no branch
            self.label = u"UNKNOWN"

        # Close common datasets
        listitem.setPath(path)
        self.property._close(listitem)
        self.context._close(listitem)
        self.info._close(listitem, self._content_type)
        self.art._close(listitem, isfolder)

        # Return a tuple compatible with 'xbmcplugin.addDirectoryItems'
        return path, listitem, isfolder

    @classmethod
    def from_dict(
            cls,
            callback,
            label,
            art=None,
            info=None,
            stream=None,
            context=None,
            properties=None,
            params=None,
            subtitles=None
    ):
        """
        Constructor to create a "listitem".
        This method will create and populate a listitem from a set of given values.
        :param Callback callback: The "callback" function or playable URL.
        :param str label: The listitem's label.
        :param dict art: Dictionary of listitem art.
        :param dict info: Dictionary of infoLabels.
        :param dict stream: Dictionary of stream details.
        :param list context: List of "context menu" item(s) containing "tuples" of ("label", "command") pairs.
        :param dict properties: Dictionary of listitem properties.
        :param dict params: Dictionary of parameters that will be passed to the "callback" function.
        :param list subtitles: List of paths to subtitle files.
        :return: A listitem object.
        :rtype: Listitem
        :example:
            >>> params = {"url": "http://example.com"}
            >>> item = {"label": "Video Title", "art": {"thumb": "http://example.com/image.jpg"}, "params": params}
            >>> listitem = Listitem.from_dict(**item)
        """
        item = cls()
        item.label = label

        if isinstance(callback, str) and "://" in callback:
            item.set_path(callback)
        else:
            item.set_callback(callback)

        if params:  # pragma: no branch
            item.params.update(params)
        if info:  # pragma: no branch
            item.info.update(info)
        if art:  # pragma: no branch
            item.art.update(art)
        if stream:  # pragma: no branch
            item.stream.update(stream)
        if properties:  # pragma: no branch
            item.property.update(properties)
        if context:  # pragma: no branch
            item.context.extend(context)
        if subtitles:  # pragma: no branch
            item.subtitles.extend(subtitles)

        return item

    @classmethod
    def next_page(cls, *args, **kwargs):
        """
        Constructor for adding link to "Next Page" of content.
        By default the current running "callback" will be called with all of the parameters that are given here.
        You can specify which "callback" will be called by setting a keyword only argument called 'callback'.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        :example:
            >>> item = Listitem()
            >>> item.next_page(url="http://example.com/videos?page2")
        """
        # Current running callback
        callback = kwargs.pop("callback") if "callback" in kwargs else dispatcher.get_route().callback

        # Add support params to callback params
        kwargs["_updatelisting_"] = True if u"_nextpagecount_" in dispatcher.params else False
        kwargs["_title_"] = dispatcher.params.get(u"_title_", u"")
        kwargs["_nextpagecount_"] = dispatcher.params.get(u"_nextpagecount_", 1) + 1

        # Create listitem instance
        item = cls()
        label = u"%s %i" % (Script.localize(localized.NEXT_PAGE), kwargs["_nextpagecount_"])
        item.info["plot"] = Script.localize(localized.NEXT_PAGE_PLOT)
        item.label = bold(label)
        item.art.global_thumb("next.png")
        item.set_callback(callback, *args, **kwargs)
        return item

    @classmethod
    def recent(cls, callback, *args, **kwargs):
        """
        Constructor for adding "Recent Videos" folder.
        This is a convenience method that creates the listitem with "name", "thumbnail" and "plot", already preset.
        :param Callback callback: The "callback" function.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        """
        # Create listitem instance
        item = cls()
        item.label = bold(Script.localize(localized.RECENT_VIDEOS))
        item.info["plot"] = Script.localize(localized.RECENT_VIDEOS_PLOT)
        item.art.global_thumb("recent.png")
        item.set_callback(callback, *args, **kwargs)
        return item

    @classmethod
    def search(cls, callback, *args, **kwargs):
        """
        Constructor to add "saved search" support to add-on.
        This will first link to a "sub" folder that lists all saved "search terms". From here,
        "search terms" can be created or removed. When a selection is made, the "callback" function
        that was given will be executed with all parameters forwarded on. Except with one extra
        parameter, ``search_query``, which is the "search term" that was selected.
        :param Callback callback: Function that will be called when the "listitem" is activated.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        """
        if hasattr(callback, "route"):
            route = callback.route
        elif isinstance(callback, CallbackRef):
            route = callback
        else:
            route = dispatcher.get_route(callback)

        kwargs["first_load"] = True
        kwargs["_route"] = route.path

        item = cls()
        item.label = bold(Script.localize(localized.SEARCH))
        item.art.global_thumb("search.png")
        item.info["plot"] = Script.localize(localized.SEARCH_PLOT)
        item.set_callback(Route.ref("/codequick/search:saved_searches"), *args, **kwargs)
        return item

    @classmethod
    def youtube(cls, content_id, label=None, enable_playlists=True):
        """
        Constructor to add a "YouTube channel" to add-on.
        This listitem will list all videos from a "YouTube", channel or playlist. All videos will have a
        "Related Videos" option via the context menu. If ``content_id`` is a channel ID and ``enable_playlists``
        is ``True``, then a link to the "channel playlists" will also be added to the list of videos.
        :param str content_id: Channel ID or playlist ID, of video content.
        :param str label: [opt] Listitem Label. (default => "All Videos").
        :param bool enable_playlists: [opt] Set to ``False`` to disable linking to channel playlists.
                                      (default => ``True``)
        :example:
            >>> item = Listitem()
            >>> item.youtube("UC4QZ_LsYcvcq7qOsOhpAX4A")
        """
        # Youtube exists, Creating listitem link
        item = cls()
        item.label = label if label else bold(Script.localize(localized.ALLVIDEOS))
        item.art.global_thumb("videos.png")
        item.params["contentid"] = content_id
        item.params["enable_playlists"] = False if content_id.startswith("PL") else enable_playlists
        item.set_callback(Route.ref("/codequick/youtube:playlist"))
        return item

    def __repr__(self):
        """Returns representation of the object."""
        return "{}('{}')".format(self.__class__.__name__, ensure_native_str(self.label))